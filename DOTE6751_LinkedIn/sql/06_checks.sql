-- =====================================================================
-- LinkedIn (reverse-engineered) | 06_checks.sql
-- Twelve acceptance checks. Every row must read PASS.
-- =====================================================================
USE linkedin_db;
SET NAMES utf8mb4;

SELECT 'C01 tables present' AS check_name,
       (SELECT COUNT(*) FROM information_schema.tables
         WHERE table_schema='linkedin_db' AND table_type='BASE TABLE') AS found,
       12 AS expected,
       IF((SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema='linkedin_db' AND table_type='BASE TABLE')=12,'PASS','FAIL') AS status
UNION ALL
SELECT 'C02 views and triggers present',
       (SELECT COUNT(*) FROM information_schema.views WHERE table_schema='linkedin_db')
     + (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='linkedin_db'),
       8,
       IF((SELECT COUNT(*) FROM information_schema.views WHERE table_schema='linkedin_db')
        + (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='linkedin_db')=8,'PASS','FAIL')
UNION ALL
SELECT 'C03 no decision before the application',
       (SELECT COUNT(*) FROM application WHERE decided_at IS NOT NULL AND decided_at < applied_at), 0,
       IF((SELECT COUNT(*) FROM application WHERE decided_at IS NOT NULL AND decided_at < applied_at)=0,'PASS','FAIL')
UNION ALL
SELECT 'C04 terminal applications carry a decision date',
       (SELECT COUNT(*) FROM application
         WHERE status IN ('HIRED','REJECTED','WITHDRAWN') AND decided_at IS NULL), 0,
       IF((SELECT COUNT(*) FROM application
            WHERE status IN ('HIRED','REJECTED','WITHDRAWN') AND decided_at IS NULL)=0,'PASS','FAIL')
UNION ALL
SELECT 'C05 in-flight applications carry no decision date',
       (SELECT COUNT(*) FROM application
         WHERE status IN ('SUBMITTED','SCREENING','INTERVIEW') AND decided_at IS NOT NULL), 0,
       IF((SELECT COUNT(*) FROM application
            WHERE status IN ('SUBMITTED','SCREENING','INTERVIEW') AND decided_at IS NOT NULL)=0,'PASS','FAIL')
UNION ALL
SELECT 'C06 hires never exceed openings',
       (SELECT COUNT(*) FROM (
          SELECT a.job_id
          FROM application a
          WHERE a.status='HIRED'
          GROUP BY a.job_id
          HAVING COUNT(*) > (SELECT j.openings FROM job_posting j WHERE j.job_id=a.job_id)
        ) t), 0,
       IF((SELECT COUNT(*) FROM (
             SELECT a.job_id FROM application a WHERE a.status='HIRED'
             GROUP BY a.job_id
             HAVING COUNT(*) > (SELECT j.openings FROM job_posting j WHERE j.job_id=a.job_id)
           ) t)=0,'PASS','FAIL')
UNION ALL
SELECT 'C07 no self-connection',
       (SELECT COUNT(*) FROM connection WHERE member_a_id = member_b_id), 0,
       IF((SELECT COUNT(*) FROM connection WHERE member_a_id = member_b_id)=0,'PASS','FAIL')
UNION ALL
SELECT 'C08 no duplicate undirected connection',
       (SELECT COUNT(*) FROM (
          SELECT LEAST(member_a_id, member_b_id) a, GREATEST(member_a_id, member_b_id) b
          FROM connection GROUP BY a, b HAVING COUNT(*) > 1
        ) t), 0,
       IF((SELECT COUNT(*) FROM (
             SELECT LEAST(member_a_id, member_b_id) a, GREATEST(member_a_id, member_b_id) b
             FROM connection GROUP BY a, b HAVING COUNT(*) > 1
           ) t)=0,'PASS','FAIL')
UNION ALL
SELECT 'C09 proficiency stays in range',
       (SELECT COUNT(*) FROM member_skill WHERE proficiency < 1 OR proficiency > 5), 0,
       IF((SELECT COUNT(*) FROM member_skill WHERE proficiency < 1 OR proficiency > 5)=0,'PASS','FAIL')
UNION ALL
SELECT 'C10 interview scores stay in range',
       (SELECT COUNT(*) FROM interview WHERE score IS NOT NULL AND (score < 1 OR score > 5)), 0,
       IF((SELECT COUNT(*) FROM interview WHERE score IS NOT NULL AND (score < 1 OR score > 5))=0,'PASS','FAIL')
UNION ALL
SELECT 'C11 every referral comes from inside the hiring company',
       (SELECT COUNT(*) FROM referral r
          JOIN application a ON a.application_id = r.application_id
          JOIN job_posting j ON j.job_id = a.job_id
         WHERE NOT EXISTS (SELECT 1 FROM experience e
                            WHERE e.member_id = r.referrer_id
                              AND e.company_id = j.company_id
                              AND e.is_current = 1)), 0,
       IF((SELECT COUNT(*) FROM referral r
             JOIN application a ON a.application_id = r.application_id
             JOIN job_posting j ON j.job_id = a.job_id
            WHERE NOT EXISTS (SELECT 1 FROM experience e
                               WHERE e.member_id = r.referrer_id
                                 AND e.company_id = j.company_id
                                 AND e.is_current = 1))=0,'PASS','FAIL')
UNION ALL
SELECT 'C12 one current employer per member',
       (SELECT COUNT(*) FROM (
          SELECT member_id FROM experience WHERE is_current = 1
          GROUP BY member_id HAVING COUNT(*) > 1
        ) t), 0,
       IF((SELECT COUNT(*) FROM (
             SELECT member_id FROM experience WHERE is_current = 1
             GROUP BY member_id HAVING COUNT(*) > 1
           ) t)=0,'PASS','FAIL');
