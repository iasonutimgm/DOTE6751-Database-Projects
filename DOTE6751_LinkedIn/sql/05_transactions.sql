-- =====================================================================
-- LinkedIn (reverse-engineered) | 05_transactions.sql
-- Transactional episodes. Everything is rolled back on purpose, so
-- running this file leaves the data exactly as it was.
-- =====================================================================
USE linkedin_db;
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------
-- D1. Moving an application forward is one atomic step: status and the
--     decision timestamp move together or not at all. The guard trigger
--     clears decided_at while the application is still in flight, which is
--     exactly the behaviour we want: a timestamp only exists once a human
--     has decided something.
-- ---------------------------------------------------------------------
SET @app = (SELECT application_id FROM application
             WHERE status = 'SCREENING' ORDER BY application_id LIMIT 1);

SELECT 'D1 before' AS step, application_id, status, decided_at
FROM application WHERE application_id = @app;

START TRANSACTION;
UPDATE application SET status = 'INTERVIEW', decided_at = applied_at + INTERVAL 3 DAY
 WHERE application_id = @app;
SELECT 'D1 inside' AS step, application_id, status, decided_at
FROM application WHERE application_id = @app;
ROLLBACK;

SELECT 'D1 after rollback' AS step, application_id, status, decided_at
FROM application WHERE application_id = @app;

-- ---------------------------------------------------------------------
-- D2. A referral is only legal from someone who works at the hiring
--     company. Run the statement by hand to see the guard:
--
--     INSERT INTO referral (application_id, referrer_id, relationship,
--                           referred_at, bonus_amount, bonus_status)
--     VALUES (1, 1, 'OTHER', NOW(), 0, 'NONE');
--       -> ERROR 1644: referrer is not employed by the hiring company
--
--     The query below counts how many existing referrals satisfy the rule,
--     which should be all of them.
-- ---------------------------------------------------------------------
SELECT 'D2 referrals' AS step,
       (SELECT COUNT(*) FROM referral) AS referrals,
       (SELECT COUNT(*)
          FROM referral r
          JOIN application a ON a.application_id = r.application_id
          JOIN job_posting j ON j.job_id = a.job_id
          JOIN experience e  ON e.member_id = r.referrer_id
         WHERE e.company_id = j.company_id AND e.is_current = 1) AS legal_referrals;

-- ---------------------------------------------------------------------
-- D3. An interview cannot be scheduled before the application reaches the
--     interview stage. Try it by hand:
--
--     INSERT INTO interview (application_id, round_no, interview_type,
--                            scheduled_at, duration_min, interviewer_id, outcome)
--     VALUES (9, 1, 'PHONE', NOW() + INTERVAL 2 DAY, 30, 1, 'PENDING');
--       -> ERROR 1644: application has not reached the interview stage
--
--     The check below shows the invariant holding over the whole table.
-- ---------------------------------------------------------------------
SELECT 'D3 stage check' AS step,
       COUNT(*) AS interviews_on_early_applications
FROM interview i
JOIN application a ON a.application_id = i.application_id
WHERE a.status IN ('SUBMITTED','SCREENING');

-- ---------------------------------------------------------------------
-- D4. A hire, simulated and rolled back: the funnel moves, then the data
--     returns to its previous state.
-- ---------------------------------------------------------------------
SET @app4 = (SELECT application_id FROM application
              WHERE status = 'OFFER' ORDER BY application_id LIMIT 1);

SELECT 'D4 before' AS step, application_id, status, decided_at
FROM application WHERE application_id = @app4;

START TRANSACTION;
UPDATE application SET status = 'HIRED', decided_at = NOW() WHERE application_id = @app4;
SELECT 'D4 inside' AS step, status, decided_at FROM application WHERE application_id = @app4;
ROLLBACK;

SELECT 'D4 after rollback' AS step, status, decided_at FROM application WHERE application_id = @app4;
