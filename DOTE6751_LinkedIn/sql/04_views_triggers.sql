-- =====================================================================
-- LinkedIn, reverse-engineered | 04_views_triggers.sql
-- MySQL 8.0  |  utf8mb4
--
-- Two mechanisms that a pure DDL schema cannot express:
--   * the application state machine (transitions, not values);
--   * cross-table business rules (a referrer must work where the job is;
--     an interview may only exist for an application that reached the
--     interview stage).
-- Views are the read side: the four shapes the 18 queries and any future
-- reporting layer keep asking for.
--
-- Apply after 02_seed.sql: the triggers validate every write, and a few
-- seeded rows (a withdrawn application that had already interviewed) are
-- legal as historical records but would be refused as fresh inserts.
-- Load order is therefore 01 -> 02 -> 04 -> 03.
-- =====================================================================

USE linkedin_db;
SET NAMES utf8mb4;

DROP VIEW  IF EXISTS v_member_current_employer;
DROP VIEW  IF EXISTS v_open_job_card;
DROP VIEW  IF EXISTS v_job_funnel;
DROP VIEW  IF EXISTS v_skill_demand_supply;

DROP TRIGGER IF EXISTS trg_application_before_insert;
DROP TRIGGER IF EXISTS trg_application_status_guard;
DROP TRIGGER IF EXISTS trg_interview_before_insert;
DROP TRIGGER IF EXISTS trg_referral_before_insert;

-- ---------------------------------------------------------------------
-- Views
-- ---------------------------------------------------------------------

-- The member as the product shows it: one row per member, current
-- employer resolved from experience (there is at most one current row,
-- guaranteed by uk_exp_one_current).
CREATE VIEW v_member_current_employer AS
SELECT m.member_id,
       m.full_name,
       m.headline,
       m.city,
       m.country,
       m.years_experience,
       m.open_to_work,
       c.company_id   AS current_company_id,
       c.company_name AS current_company,
       c.industry     AS current_industry
FROM member m
LEFT JOIN experience  e ON e.member_id = m.member_id AND e.is_current = 1
LEFT JOIN company     c ON c.company_id = e.company_id;

-- A job card: everything a search result renders, in one row.
CREATE VIEW v_open_job_card AS
SELECT j.job_id,
       j.title,
       j.seniority,
       j.work_mode,
       j.city,
       j.country,
       j.salary_min,
       j.salary_max,
       j.currency,
       j.openings,
       j.posted_at,
       c.company_id,
       c.company_name,
       c.industry,
       c.is_verified,
       m.full_name  AS recruiter_name,
       (SELECT COUNT(*) FROM job_skill s WHERE s.job_id = j.job_id) AS skills_asked,
       (SELECT COUNT(*) FROM application a WHERE a.job_id = j.job_id) AS applicants
FROM job_posting j
JOIN company c ON c.company_id = j.company_id
JOIN member  m ON m.member_id  = j.recruiter_id
WHERE j.status = 'OPEN';

-- Funnel per posting, materialised as counts so a dashboard does not have
-- to re-aggregate 250 applications on every page view.
CREATE VIEW v_job_funnel AS
SELECT j.job_id,
       j.title,
       j.company_id,
       SUM(a.status = 'SUBMITTED')  AS submitted,
       SUM(a.status = 'SCREENING')  AS screening,
       SUM(a.status = 'INTERVIEW')  AS interviewing,
       SUM(a.status = 'OFFER')      AS offered,
       SUM(a.status = 'HIRED')      AS hired,
       SUM(a.status = 'REJECTED')   AS rejected,
       SUM(a.status = 'WITHDRAWN')  AS withdrawn,
       COUNT(a.application_id)      AS applications
FROM job_posting j
LEFT JOIN application a ON a.job_id = j.job_id
GROUP BY j.job_id, j.title, j.company_id;

-- Demand (postings asking for a skill) against supply (members claiming
-- it at proficiency >= 4).  Both sides are pre-aggregated so the view is
-- cheap to scan; Q17 uses the same shape with a stricter definition.
CREATE VIEW v_skill_demand_supply AS
SELECT s.skill_id,
       s.skill_name,
       s.skill_family,
       (SELECT COUNT(*) FROM job_skill  js WHERE js.skill_id = s.skill_id) AS postings_asking,
       (SELECT COUNT(*) FROM member_skill ms
         WHERE ms.skill_id = s.skill_id AND ms.proficiency >= 4)           AS strong_holders
FROM skill s;

-- ---------------------------------------------------------------------
-- Trigger 1: an application must be born in a state that matches its
-- decided_at, and cannot be dated before the posting existed.
-- ---------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_application_before_insert
BEFORE INSERT ON application
FOR EACH ROW
BEGIN
  DECLARE v_posted DATETIME;

  IF NEW.status IN ('HIRED', 'REJECTED', 'WITHDRAWN') AND NEW.decided_at IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'application: a final status requires decided_at';
  END IF;

  IF NEW.status IN ('SUBMITTED', 'SCREENING', 'INTERVIEW') AND NEW.decided_at IS NOT NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'application: an open status must not carry decided_at';
  END IF;

  SELECT posted_at INTO v_posted FROM job_posting WHERE job_id = NEW.job_id;
  IF v_posted IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'application: unknown job_id';
  END IF;
  IF NEW.applied_at < v_posted THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'application: applied_at precedes the posting date';
  END IF;
END$$

-- ---------------------------------------------------------------------
-- Trigger 2: the state machine.  Only the arrows of the hiring loop are
-- legal, and reaching a terminal state stamps decided_at automatically.
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_application_status_guard
BEFORE UPDATE ON application
FOR EACH ROW
BEGIN
  IF NEW.job_id <> OLD.job_id OR NEW.member_id <> OLD.member_id THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'application: job_id and member_id are immutable';
  END IF;

  IF NEW.status <> OLD.status THEN
    IF NOT (
         (OLD.status = 'SUBMITTED' AND NEW.status IN ('SCREENING', 'REJECTED', 'WITHDRAWN'))
      OR (OLD.status = 'SCREENING' AND NEW.status IN ('INTERVIEW', 'REJECTED', 'WITHDRAWN'))
      OR (OLD.status = 'INTERVIEW' AND NEW.status IN ('OFFER', 'REJECTED', 'WITHDRAWN'))
      OR (OLD.status = 'OFFER'     AND NEW.status IN ('HIRED', 'REJECTED', 'WITHDRAWN'))
    ) THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'application: illegal status transition';
    END IF;

    IF NEW.status IN ('HIRED', 'REJECTED', 'WITHDRAWN') THEN
      SET NEW.decided_at = COALESCE(NEW.decided_at, NOW());
    ELSE
      SET NEW.decided_at = NULL;
    END IF;
  END IF;
END$$

-- ---------------------------------------------------------------------
-- Trigger 3: an interview exists only for an application that has
-- reached the interview stage, is scheduled after the application date,
-- and takes the next free round number.
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_interview_before_insert
BEFORE INSERT ON interview
FOR EACH ROW
BEGIN
  DECLARE v_status   VARCHAR(12);
  DECLARE v_applied  DATETIME;
  DECLARE v_maxround TINYINT;

  SELECT status, applied_at INTO v_status, v_applied
  FROM application WHERE application_id = NEW.application_id;

  IF v_status IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'interview: unknown application_id';
  END IF;
  IF v_status NOT IN ('INTERVIEW', 'OFFER', 'HIRED', 'REJECTED') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'interview: application has not reached the interview stage';
  END IF;
  IF NEW.scheduled_at < v_applied THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'interview: scheduled before the application date';
  END IF;

  SELECT COALESCE(MAX(round_no), 0) INTO v_maxround
  FROM interview WHERE application_id = NEW.application_id;

  IF NEW.round_no <> v_maxround + 1 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'interview: rounds must be numbered 1..n without gaps';
  END IF;
END$$

-- ---------------------------------------------------------------------
-- Trigger 4: a referral is an internal recommendation.  The application
-- must have arrived through the referral channel, the referrer must not
-- be the candidate, and the referrer must currently work at the company
-- that owns the posting.  (A CHECK cannot see the other tables.)
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_referral_before_insert
BEFORE INSERT ON referral
FOR EACH ROW
BEGIN
  DECLARE v_candidate INT;
  DECLARE v_channel   VARCHAR(10);
  DECLARE v_company   INT;

  SELECT a.member_id, a.source_channel, j.company_id
    INTO v_candidate, v_channel, v_company
  FROM application a
  JOIN job_posting j ON j.job_id = a.job_id
  WHERE a.application_id = NEW.application_id;

  IF v_candidate IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'referral: unknown application_id';
  END IF;
  IF v_channel <> 'REFERRAL' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'referral: the application is not flagged as a referral';
  END IF;
  IF NEW.referrer_id = v_candidate THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'referral: a candidate cannot refer themselves';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM experience e
                  WHERE e.member_id = NEW.referrer_id
                    AND e.company_id = v_company
                    AND e.is_current = 1) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'referral: the referrer does not work at the hiring company';
  END IF;
END$$

DELIMITER ;

-- ---------------------------------------------------------------------
-- Self-test, safe to run: prints the object inventory.
-- ---------------------------------------------------------------------
SELECT 'view'   AS kind, table_name AS name FROM information_schema.views
 WHERE table_schema = 'linkedin_db'
UNION ALL
SELECT 'trigger', trigger_name FROM information_schema.triggers
 WHERE trigger_schema = 'linkedin_db'
ORDER BY kind, name;
