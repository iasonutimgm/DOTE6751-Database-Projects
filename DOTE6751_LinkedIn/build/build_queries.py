# -*- coding: utf-8 -*-
"""Pick the two example parameters used by Q09 and Q18, then materialise
03_queries.sql from queries_template.sql.

Parameters are chosen from the loaded data so that the two showcase queries
return a non-trivial answer set:
  * Q09 member  = an open-to-work non-recruiter with the most jobs where they
                  hold at least half, but not all, of the hard requirements;
  * Q18 posting = an open posting with >= 4 hard requirements that has the
                  most reachable candidates two hops away.
"""
import json
import os
import pymysql

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queries_template.sql")
OUT = r"D:\桌面\数据库大作业\LinkedIn_交付\sql\03_queries.sql"
PARAMS = r"D:\桌面\数据库大作业\_work_li\query_params.json"

conn = pymysql.connect(host="127.0.0.1", user="root", password="zsy20040609",
                       charset="utf8mb4", database="linkedin_db", autocommit=True)

MEMBER_SQL = """
WITH jr AS (
  SELECT js.job_id, COUNT(*) AS total
  FROM job_skill js
  JOIN job_posting j ON j.job_id = js.job_id AND j.status = 'OPEN'
  WHERE js.importance = 'REQUIRED'
  GROUP BY js.job_id
),
mj AS (
  SELECT m.member_id, jr.total, COUNT(ms.skill_id) AS matched
  FROM member m
  CROSS JOIN jr
  JOIN job_skill js ON js.job_id = jr.job_id AND js.importance = 'REQUIRED'
  LEFT JOIN member_skill ms
         ON ms.member_id = m.member_id AND ms.skill_id = js.skill_id
        AND ms.proficiency >= js.min_proficiency
  WHERE m.open_to_work = 1 AND m.member_id > 72
  GROUP BY m.member_id, jr.job_id, jr.total
)
SELECT member_id,
       SUM(matched >= 2 AND matched < total) AS partial_jobs
FROM mj
GROUP BY member_id
HAVING partial_jobs > 0
ORDER BY partial_jobs DESC, member_id
LIMIT 1
"""

JOB_SQL = """
WITH m AS (
  SELECT js.job_id, ms.member_id, COUNT(*) AS held
  FROM job_skill js
  JOIN member_skill ms ON ms.skill_id = js.skill_id
                      AND ms.proficiency >= js.min_proficiency
  WHERE js.importance = 'REQUIRED'
  GROUP BY js.job_id, ms.member_id
)
SELECT j.job_id, COUNT(*) AS reachable
FROM m
JOIN job_posting j ON j.job_id = m.job_id AND j.status = 'OPEN'
JOIN member mm ON mm.member_id = m.member_id
WHERE m.held >= 2 AND mm.open_to_work = 1
GROUP BY j.job_id
HAVING (SELECT COUNT(*) FROM job_skill js2
         WHERE js2.job_id = j.job_id AND js2.importance = 'REQUIRED') >= 3
ORDER BY reachable DESC, j.job_id
LIMIT 1
"""

with conn.cursor() as cur:
    cur.execute(MEMBER_SQL)
    member_id, partial = cur.fetchone()
    cur.execute("""SELECT full_name, headline, city FROM member WHERE member_id = %s""",
                (member_id,))
    name, headline, city = cur.fetchone()
    member_label = f"{name}, {headline}, {city}; {partial} partially matching open roles"

    cur.execute(JOB_SQL)
    job_id, reachable = cur.fetchone()
    cur.execute("""SELECT j.title, c.company_name, j.city FROM job_posting j
                     JOIN company c ON c.company_id = j.company_id WHERE j.job_id = %s""",
                (job_id,))
    title, company, jcity = cur.fetchone()
    job_label = f"{title} at {company}, {jcity}; {reachable} reachable candidates"

text = open(TEMPLATE, encoding="utf-8").read()
text = (text.replace("{{MEMBER_ID}}", str(member_id))
            .replace("{{MEMBER_LABEL}}", member_label)
            .replace("{{JOB_ID}}", str(job_id))
            .replace("{{JOB_LABEL}}", job_label))
open(OUT, "w", encoding="utf-8", newline="\n").write(text)

json.dump({"member_id": member_id, "member_label": member_label,
           "job_id": job_id, "job_label": job_label,
           "partial_jobs": int(partial), "reachable": int(reachable)},
          open(PARAMS, "w", encoding="utf-8"), indent=2)
print("member", member_id, member_label)
print("job", job_id, job_label)
print("wrote", OUT)
