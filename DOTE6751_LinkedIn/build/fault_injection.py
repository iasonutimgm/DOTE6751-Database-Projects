# -*- coding: utf-8 -*-
"""Fault injection: prove that each constraint actually refuses bad data.

Every statement runs inside its own transaction and is rolled back, so the
database is unchanged afterwards.  The captured error code and message are
written to _work_li/fault_injection.json and quoted in
design/Constraint_Inventory.md and in the File_Guide.
"""
import json
import pymysql

CASES = [
    ("F1", "duplicate application for the same posting",
     """INSERT INTO application (job_id, member_id, source_channel, status, applied_at)
        SELECT a.job_id, a.member_id, 'DIRECT', 'SUBMITTED', a.applied_at
        FROM application a LIMIT 1"""),
    ("F2", "salary band inverted on a posting",
     """INSERT INTO job_posting (company_id, recruiter_id, title, seniority, city, country,
                                  salary_min, salary_max, posted_at)
        VALUES (1, 1, 'Test Role', 'MID', 'Austin', 'US', 200000, 100000, '2026-09-01 10:00:00')"""),
    ("F3", "second current experience for the same member",
     """INSERT INTO experience (member_id, company_id, title, start_date, is_current)
        VALUES (1, 2, 'Another Job', '2026-01-01', 1)"""),
    ("F4", "self-loop connection",
     """INSERT INTO connection (member_a_id, member_b_id, connected_at)
        VALUES (5, 5, '2026-09-01 10:00:00')"""),
    ("F5", "application to a posting that does not exist",
     """INSERT INTO application (job_id, member_id, status, applied_at)
        VALUES (99999, 5, 'SUBMITTED', '2026-09-01 10:00:00')"""),
    ("F6", "decision dated before the application",
     """INSERT INTO application (job_id, member_id, status, applied_at, decided_at)
        VALUES (3, 4, 'REJECTED', '2026-09-10 10:00:00', '2026-09-01 10:00:00')"""),
    ("F7", "interview score outside 1-5",
     """UPDATE interview SET score = 9 WHERE outcome = 'PASS' LIMIT 1"""),
    ("F8", "terminal status without a decision timestamp",
     """INSERT INTO application (job_id, member_id, status, applied_at)
        VALUES (3, 7, 'HIRED', '2026-09-01 10:00:00')"""),
    ("F9", "illegal status jump SUBMITTED -> HIRED",
     """UPDATE application SET status = 'HIRED', decided_at = '2026-09-20 10:00:00'
        WHERE status = 'SUBMITTED' LIMIT 1"""),
    ("F10", "interview before the application was submitted",
     """INSERT INTO interview (application_id, round_no, interview_type, scheduled_at,
                               duration_min, interviewer_id, outcome, score)
        SELECT a.application_id, 1, 'PHONE', a.applied_at - INTERVAL 3 DAY, 30, 2, 'PASS', 4
        FROM application a WHERE a.status = 'INTERVIEW' LIMIT 1"""),
    ("F11", "referral for an application that did not come through referral",
     """INSERT INTO referral (application_id, referrer_id, relationship, referred_at,
                              bonus_amount, bonus_status)
        SELECT a.application_id, 1, 'COLLEAGUE', a.applied_at, 2000, 'PENDING'
        FROM application a WHERE a.source_channel = 'DIRECT' LIMIT 1"""),
    ("F12", "referrer who does not work at the hiring company",
     """INSERT INTO referral (application_id, referrer_id, relationship, referred_at,
                              bonus_amount, bonus_status)
        SELECT a.application_id, 300, 'FRIEND', a.applied_at, 2000, 'PENDING'
        FROM application a WHERE a.source_channel = 'REFERRAL' LIMIT 1"""),
    ("F13", "deleting a member who has already interviewed candidates",
     """DELETE m FROM member m
          JOIN (SELECT interviewer_id FROM interview LIMIT 1) x
            ON x.interviewer_id = m.member_id"""),
    ("F14", "negative referral bonus",
     """UPDATE referral SET bonus_amount = -100 LIMIT 1"""),
]

conn = pymysql.connect(host="127.0.0.1", user="root", password="zsy20040609",
                       charset="utf8mb4", database="linkedin_db", autocommit=False)
results = []
for fid, label, sql in CASES:
    with conn.cursor() as cur:
        try:
            cur.execute(sql)
            results.append(dict(id=fid, fault=label, blocked=False, code=0,
                                error="NO ERROR - the statement was accepted"))
        except pymysql.MySQLError as e:
            results.append(dict(id=fid, fault=label, blocked=True, code=e.args[0],
                                error=str(e.args[1] if len(e.args) > 1 else e)))
    conn.rollback()

for r in results:
    status = "BLOCKED" if r["blocked"] else "ACCEPTED (!)"
    print(f"{r['id']:4s} {status:10s} errno={r['code']:<6} {r['fault']}")
    print(f"      {r['error']}")

json.dump(results, open(r"D:\桌面\数据库大作业\_work_li\fault_injection.json", "w",
                        encoding="utf-8"), indent=2, ensure_ascii=False)

with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM application")
    print("\napplications after rollback:", cur.fetchone()[0])
conn.close()
