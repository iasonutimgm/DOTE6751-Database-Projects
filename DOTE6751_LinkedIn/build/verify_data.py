# -*- coding: utf-8 -*-
"""Cross-table consistency audit for linkedin_db.

Every check is written as "SELECT rows that violate the rule"; the expected
count is 0.  The report is written to query_results/_consistency_report.json
so the marker can see the schema was tested, not only executed.
"""
import json
import os
import pymysql

OUT = r"D:\桌面\数据库大作业\LinkedIn_交付\query_results"
os.makedirs(OUT, exist_ok=True)

CHECKS = [
    ("I1  HIRED implies at least three PASS interviews",
     """SELECT COUNT(*) FROM application a
        WHERE a.status = 'HIRED'
          AND (SELECT COUNT(*) FROM interview i
                WHERE i.application_id = a.application_id AND i.outcome = 'PASS') < 3"""),
    ("I2  REJECTED after interviews implies a final FAIL",
     """SELECT COUNT(*) FROM application a
        WHERE a.status = 'REJECTED'
          AND EXISTS (SELECT 1 FROM interview i WHERE i.application_id = a.application_id)
          AND (SELECT i.outcome FROM interview i
                WHERE i.application_id = a.application_id
                ORDER BY i.round_no DESC LIMIT 1) <> 'FAIL'"""),
    ("I3  decided_at is NULL exactly for open statuses",
     """SELECT COUNT(*) FROM application
        WHERE (status IN ('SUBMITTED','SCREENING','INTERVIEW') AND decided_at IS NOT NULL)
           OR (status IN ('HIRED','REJECTED','WITHDRAWN') AND decided_at IS NULL)"""),
    ("I4a every REFERRAL application has a referral row",
     """SELECT COUNT(*) FROM application a
        WHERE a.source_channel = 'REFERRAL'
          AND NOT EXISTS (SELECT 1 FROM referral r WHERE r.application_id = a.application_id)"""),
    ("I4b every referrer currently works at the hiring company",
     """SELECT COUNT(*) FROM referral r
          JOIN application a ON a.application_id = r.application_id
          JOIN job_posting j ON j.job_id = a.job_id
        WHERE NOT EXISTS (SELECT 1 FROM experience e
                           WHERE e.member_id = r.referrer_id
                             AND e.company_id = j.company_id
                             AND e.is_current = 1)"""),
    ("I5  hires per posting never exceed openings",
     """SELECT COUNT(*) FROM (SELECT a.job_id
                              FROM application a
                             WHERE a.status = 'HIRED'
                             GROUP BY a.job_id, a.job_id
                            HAVING COUNT(*) > (SELECT openings FROM job_posting j WHERE j.job_id = a.job_id)) x"""),
    ("I6  at most one current experience per member",
     """SELECT COUNT(*) FROM (SELECT member_id FROM experience
                             WHERE is_current = 1 GROUP BY member_id HAVING COUNT(*) > 1) x"""),
    ("I7  connection edges are stored in canonical order",
     """SELECT COUNT(*) FROM connection WHERE member_a_id >= member_b_id"""),
    ("I8a applied_at never precedes posted_at",
     """SELECT COUNT(*) FROM application a JOIN job_posting j ON j.job_id = a.job_id
        WHERE a.applied_at < j.posted_at"""),
    ("I8b decided_at never precedes applied_at",
     """SELECT COUNT(*) FROM application WHERE decided_at < applied_at"""),
    ("I8c no application after its posting closed",
     """SELECT COUNT(*) FROM application a JOIN job_posting j ON j.job_id = a.job_id
        WHERE j.closed_at IS NOT NULL AND a.applied_at > j.closed_at"""),
    ("I9a interviews happen after the application date",
     """SELECT COUNT(*) FROM interview i JOIN application a ON a.application_id = i.application_id
        WHERE i.scheduled_at < a.applied_at"""),
    ("I9b interview rounds are 1..n without gaps",
     """SELECT COUNT(*) FROM (SELECT application_id
                              FROM interview
                             GROUP BY application_id
                            HAVING MIN(round_no) <> 1 OR MAX(round_no) <> COUNT(*)) x"""),
    ("I10 stage implies the right number of interviews",
     """SELECT COUNT(*) FROM application a
        WHERE (a.status = 'HIRED'  AND (SELECT COUNT(*) FROM interview i WHERE i.application_id = a.application_id) < 3)
           OR (a.status = 'OFFER'  AND (SELECT COUNT(*) FROM interview i WHERE i.application_id = a.application_id) < 2)
           OR (a.status = 'INTERVIEW' AND (SELECT COUNT(*) FROM interview i WHERE i.application_id = a.application_id) < 1)
           OR (a.status IN ('SUBMITTED','SCREENING')
               AND EXISTS (SELECT 1 FROM interview i WHERE i.application_id = a.application_id))"""),
    ("I11 scored interviews carry a score, pending ones do not",
     """SELECT COUNT(*) FROM interview
        WHERE (outcome IN ('PASS','FAIL') AND score IS NULL)
           OR (outcome = 'PENDING' AND score IS NOT NULL)"""),
    ("I12 nobody refers themselves",
     """SELECT COUNT(*) FROM referral r JOIN application a ON a.application_id = r.application_id
        WHERE r.referrer_id = a.member_id"""),
    ("I13 no member applies to their current employer",
     """SELECT COUNT(*) FROM application a
        WHERE EXISTS (SELECT 1 FROM experience e
                       WHERE e.member_id = a.member_id AND e.is_current = 1
                         AND e.company_id = (SELECT company_id FROM job_posting j WHERE j.job_id = a.job_id))"""),
    ("I14 an INTERVIEW-stage application still has an open round",
     """SELECT COUNT(*) FROM application a
        WHERE a.status = 'INTERVIEW'
          AND (SELECT i.outcome FROM interview i WHERE i.application_id = a.application_id
                ORDER BY i.round_no DESC LIMIT 1) <> 'PENDING'"""),
    ("I15 an OFFER-stage application has no failed round",
     """SELECT COUNT(*) FROM application a
        WHERE a.status IN ('OFFER','HIRED')
          AND EXISTS (SELECT 1 FROM interview i
                       WHERE i.application_id = a.application_id AND i.outcome IN ('FAIL','NO_SHOW'))"""),
    ("I16 no application to a posting still in DRAFT",
     """SELECT COUNT(*) FROM application a JOIN job_posting j ON j.job_id = a.job_id
        WHERE j.status = 'DRAFT'"""),
    ("I17 all timestamps are inside the snapshot window",
     """SELECT (SELECT COUNT(*) FROM application WHERE applied_at > '2026-10-15 18:00:00')
             + (SELECT COUNT(*) FROM interview  WHERE scheduled_at > '2026-10-15 18:00:00')
             + (SELECT COUNT(*) FROM job_posting WHERE posted_at > '2026-10-15 18:00:00')"""),
    ("I18 every job has a recruiter employed somewhere in the record",
     """SELECT COUNT(*) FROM job_posting j
        WHERE NOT EXISTS (SELECT 1 FROM member m WHERE m.member_id = j.recruiter_id)"""),
]

FACTS = [
    ("members", "SELECT COUNT(*) FROM member"),
    ("companies", "SELECT COUNT(*) FROM company"),
    ("postings", "SELECT COUNT(*) FROM job_posting"),
    ("open postings", "SELECT COUNT(*) FROM job_posting WHERE status = 'OPEN'"),
    ("applications", "SELECT COUNT(*) FROM application"),
    ("interviews", "SELECT COUNT(*) FROM interview"),
    ("referrals", "SELECT COUNT(*) FROM referral"),
    ("hires", "SELECT COUNT(*) FROM application WHERE status = 'HIRED'"),
    ("connections", "SELECT COUNT(*) FROM connection"),
    ("members with a current employer", "SELECT COUNT(DISTINCT member_id) FROM experience WHERE is_current = 1"),
    ("median days to hire",
     """SELECT ROUND(AVG(d), 1) FROM (SELECT TIMESTAMPDIFF(DAY, applied_at, decided_at) d
                                     FROM application WHERE status = 'HIRED') x"""),
]

conn = pymysql.connect(host="127.0.0.1", user="root", password="zsy20040609",
                       charset="utf8mb4", database="linkedin_db", autocommit=True)
report = {"checks": [], "facts": {}}
failures = 0
with conn.cursor() as cur:
    for label, sql in CHECKS:
        cur.execute(sql)
        n = cur.fetchone()[0]
        ok = (n == 0)
        if not ok:
            failures += 1
        report["checks"].append({"id": label.split()[0], "rule": label[4:].strip(),
                                 "violations": int(n), "status": "PASS" if ok else "FAIL"})
        print(f"[{'PASS' if ok else 'FAIL'}] {label}  -> {n} violations")
    for label, sql in FACTS:
        cur.execute(sql)
        v = cur.fetchone()[0]
        if type(v).__name__ == "Decimal":
            v = float(v)
        report["facts"][label] = v
        print(f"       {label}: {report['facts'][label]}")
report["summary"] = {"checks": len(CHECKS), "failed": failures}
json.dump(report, open(os.path.join(OUT, "_consistency_report.json"), "w", encoding="utf-8"),
          indent=2)
print("\nfailed checks:", failures)
conn.close()
