-- =====================================================================
-- LinkedIn, reverse-engineered: the hiring loop
-- 01_schema.sql  |  MySQL 8.0  |  utf8mb4 / utf8mb4_0900_ai_ci
-- DOTE 6751 Group Project  |  November 2026
--
-- Run order: 01_schema -> 02_seed -> 04_views_triggers -> 03_queries
-- (04 defines the triggers that 02 already satisfies, so it may also be
--  loaded before 02; 03 is read-only and can run at any point after 02.)
--
-- The schema is a logical reconstruction of a public product: the eleven
-- nouns a member can actually see (profile, company, job, application...)
-- plus the two associative tables that carry the hiring loop.  Every
-- table is in third normal form; the argument is written out per table in
-- design/Normalization_Proof.xlsx.
-- =====================================================================

DROP DATABASE IF EXISTS linkedin_db;
CREATE DATABASE linkedin_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE linkedin_db;

SET NAMES utf8mb4;

-- ---------------------------------------------------------------------
-- 1. company
--    The employer. Industry and head-count band are properties of the
--    company, not of a posting, so they live here once (3NF).
-- ---------------------------------------------------------------------
CREATE TABLE company (
  company_id    INT           NOT NULL AUTO_INCREMENT,
  company_name  VARCHAR(90)   NOT NULL,
  industry      VARCHAR(60)   NOT NULL,
  hq_country    CHAR(2)       NOT NULL,
  size_band     ENUM('1-10','11-50','51-200','201-500','501-1000','1001-5000','5001+')
                              NOT NULL DEFAULT '51-200',
  founded_year  SMALLINT      NULL,
  is_verified   TINYINT(1)    NOT NULL DEFAULT 0,
  PRIMARY KEY (company_id),
  UNIQUE KEY uk_company_name (company_name),
  KEY idx_company_industry (industry),
  CONSTRAINT ck_company_founded CHECK (founded_year IS NULL OR founded_year BETWEEN 1700 AND 2026),
  CONSTRAINT ck_company_verified CHECK (is_verified IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 2. member
--    A natural person: candidate, referrer and recruiter are the same
--    entity set seen through different relationship sets.  Current
--    employer is deliberately NOT stored here: it is derivable from
--    experience.is_current (see Design_Rationale.md, section 4).
-- ---------------------------------------------------------------------
CREATE TABLE member (
  member_id        INT           NOT NULL AUTO_INCREMENT,
  full_name        VARCHAR(80)   NOT NULL,
  headline         VARCHAR(140)  NULL,
  email            VARCHAR(120)  NOT NULL,
  country          CHAR(2)       NOT NULL,
  city             VARCHAR(60)   NOT NULL,
  years_experience TINYINT UNSIGNED NOT NULL DEFAULT 0,
  open_to_work     TINYINT(1)    NOT NULL DEFAULT 1,
  profile_visibility ENUM('PUBLIC','CONNECTIONS','PRIVATE') NOT NULL DEFAULT 'PUBLIC',
  joined_at        DATE          NOT NULL,
  PRIMARY KEY (member_id),
  UNIQUE KEY uk_member_email (email),
  KEY idx_member_city (city, country),
  KEY idx_member_open (open_to_work, years_experience),
  CONSTRAINT ck_member_years CHECK (years_experience <= 50),
  CONSTRAINT ck_member_visibility CHECK (profile_visibility IN ('PUBLIC','CONNECTIONS','PRIVATE'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 3. job_posting
--    One advertised opening.  Recruiter (the member who posted it) is a
--    separate role from the hiring company; this lets the same employer
--    be represented by several recruiters and lets a recruiter move.
-- ---------------------------------------------------------------------
CREATE TABLE job_posting (
  job_id           INT           NOT NULL AUTO_INCREMENT,
  company_id       INT           NOT NULL,
  recruiter_id     INT           NOT NULL,
  title            VARCHAR(120)  NOT NULL,
  seniority        ENUM('INTERN','JUNIOR','MID','SENIOR','LEAD','PRINCIPAL','DIRECTOR') NOT NULL,
  employment_type  ENUM('FULL_TIME','PART_TIME','CONTRACT','INTERNSHIP') NOT NULL DEFAULT 'FULL_TIME',
  work_mode        ENUM('ONSITE','HYBRID','REMOTE') NOT NULL DEFAULT 'HYBRID',
  city             VARCHAR(60)   NOT NULL,
  country          CHAR(2)       NOT NULL,
  salary_min       INT           NOT NULL,
  salary_max       INT           NOT NULL,
  currency         CHAR(3)       NOT NULL DEFAULT 'USD',
  min_years_experience TINYINT UNSIGNED NOT NULL DEFAULT 0,
  openings         TINYINT UNSIGNED NOT NULL DEFAULT 1,
  status           ENUM('DRAFT','OPEN','CLOSED','ON_HOLD') NOT NULL DEFAULT 'OPEN',
  posted_at        DATETIME      NOT NULL,
  closed_at        DATETIME      NULL,
  PRIMARY KEY (job_id),
  KEY idx_job_company_status (company_id, status),
  KEY idx_job_city (city, country),
  KEY idx_job_posted (posted_at),
  KEY idx_job_recruiter (recruiter_id),
  CONSTRAINT fk_job_company FOREIGN KEY (company_id)
    REFERENCES company (company_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_job_recruiter FOREIGN KEY (recruiter_id)
    REFERENCES member (member_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_job_salary CHECK (salary_min > 0 AND salary_max >= salary_min),
  CONSTRAINT ck_job_years CHECK (min_years_experience <= 40),
  CONSTRAINT ck_job_openings CHECK (openings BETWEEN 1 AND 50),
  CONSTRAINT ck_job_closed CHECK (closed_at IS NULL OR closed_at >= posted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 4. skill
--    Controlled vocabulary.  "skill_family" is the only classified
--    attribute; keeping the vocabulary narrow is what makes gap
--    analysis (Q09, Q12, Q18) comparable across jobs.
-- ---------------------------------------------------------------------
CREATE TABLE skill (
  skill_id    INT          NOT NULL AUTO_INCREMENT,
  skill_name  VARCHAR(60)  NOT NULL,
  skill_family ENUM('LANGUAGE','FRAMEWORK','DATABASE','CLOUD','DATA','PRODUCT','DESIGN','SOFT')
                           NOT NULL,
  is_emerging TINYINT(1)   NOT NULL DEFAULT 0,
  PRIMARY KEY (skill_id),
  UNIQUE KEY uk_skill_name (skill_name),
  KEY idx_skill_family (skill_family),
  CONSTRAINT ck_skill_emerging CHECK (is_emerging IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 5. member_skill
--    M:N between member and skill, carrying its own attributes.
--    PK is the full pair, so the relation is automatically in 3NF:
--    proficiency depends on (member, skill), not on a part of the key.
-- ---------------------------------------------------------------------
CREATE TABLE member_skill (
  member_id        INT          NOT NULL,
  skill_id         INT          NOT NULL,
  proficiency      TINYINT      NOT NULL,
  years_used       DECIMAL(3,1) NOT NULL DEFAULT 0.0,
  endorsement_count SMALLINT    NOT NULL DEFAULT 0,
  added_at         DATE         NOT NULL,
  PRIMARY KEY (member_id, skill_id),
  KEY idx_ms_skill (skill_id, proficiency),
  CONSTRAINT fk_ms_member FOREIGN KEY (member_id)
    REFERENCES member (member_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_ms_skill FOREIGN KEY (skill_id)
    REFERENCES skill (skill_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ck_ms_proficiency CHECK (proficiency BETWEEN 1 AND 5),
  CONSTRAINT ck_ms_years CHECK (years_used BETWEEN 0 AND 40),
  CONSTRAINT ck_ms_endorse CHECK (endorsement_count BETWEEN 0 AND 999)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 6. job_skill
--    M:N between posting and skill.  "importance" is the attribute that
--    lets a query distinguish a hard requirement from a nice-to-have;
--    without it the pair alone could not answer Q09.
-- ---------------------------------------------------------------------
CREATE TABLE job_skill (
  job_id          INT          NOT NULL,
  skill_id        INT          NOT NULL,
  importance      ENUM('REQUIRED','PREFERRED') NOT NULL DEFAULT 'REQUIRED',
  min_proficiency TINYINT      NOT NULL DEFAULT 3,
  PRIMARY KEY (job_id, skill_id),
  KEY idx_js_skill (skill_id, importance),
  CONSTRAINT fk_js_job FOREIGN KEY (job_id)
    REFERENCES job_posting (job_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_js_skill FOREIGN KEY (skill_id)
    REFERENCES skill (skill_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ck_js_proficiency CHECK (min_proficiency BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 7. application
--    The spine of the hiring loop.  One member may apply once per job
--    (uk_app_job_member); the status column is the state machine whose
--    legal transitions are enforced by trg_application_status_guard.
--    decided_at is the timestamp of the last state change, which is what
--    makes time-to-hire (Q10) computable without an audit table.
-- ---------------------------------------------------------------------
CREATE TABLE application (
  application_id INT          NOT NULL AUTO_INCREMENT,
  job_id         INT          NOT NULL,
  member_id      INT          NOT NULL,
  source_channel ENUM('DIRECT','REFERRAL','SOURCING') NOT NULL DEFAULT 'DIRECT',
  status         ENUM('SUBMITTED','SCREENING','INTERVIEW','OFFER','HIRED','REJECTED','WITHDRAWN')
                              NOT NULL DEFAULT 'SUBMITTED',
  applied_at     DATETIME     NOT NULL,
  decided_at     DATETIME     NULL,
  resume_version VARCHAR(20)  NOT NULL DEFAULT 'v1',
  PRIMARY KEY (application_id),
  UNIQUE KEY uk_app_job_member (job_id, member_id),
  KEY idx_app_member (member_id, status),
  KEY idx_app_job_status (job_id, status),
  KEY idx_app_applied (applied_at),
  CONSTRAINT fk_app_job FOREIGN KEY (job_id)
    REFERENCES job_posting (job_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_app_member FOREIGN KEY (member_id)
    REFERENCES member (member_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ck_app_decided CHECK (decided_at IS NULL OR decided_at >= applied_at),
  CONSTRAINT ck_app_status CHECK (status IN ('SUBMITTED','SCREENING','INTERVIEW','OFFER','HIRED','REJECTED','WITHDRAWN'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 8. interview
--    One round of one application; (application_id, round_no) is unique,
--    so a round cannot be duplicated.  score is nullable because a
--    scheduled interview has not been scored yet.
-- ---------------------------------------------------------------------
CREATE TABLE interview (
  interview_id   INT          NOT NULL AUTO_INCREMENT,
  application_id INT          NOT NULL,
  round_no       TINYINT UNSIGNED NOT NULL,
  interview_type ENUM('PHONE','VIDEO','ONSITE','TECHNICAL','HR') NOT NULL,
  scheduled_at   DATETIME     NOT NULL,
  duration_min   SMALLINT UNSIGNED NOT NULL DEFAULT 45,
  interviewer_id INT          NOT NULL,
  outcome        ENUM('PENDING','PASS','FAIL','NO_SHOW') NOT NULL DEFAULT 'PENDING',
  score          TINYINT      NULL,
  PRIMARY KEY (interview_id),
  UNIQUE KEY uk_int_app_round (application_id, round_no),
  KEY idx_int_scheduled (scheduled_at),
  KEY idx_int_interviewer (interviewer_id),
  CONSTRAINT fk_int_app FOREIGN KEY (application_id)
    REFERENCES application (application_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_int_member FOREIGN KEY (interviewer_id)
    REFERENCES member (member_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_int_round CHECK (round_no BETWEEN 1 AND 6),
  CONSTRAINT ck_int_duration CHECK (duration_min BETWEEN 15 AND 480),
  CONSTRAINT ck_int_score CHECK (score IS NULL OR score BETWEEN 1 AND 5),
  CONSTRAINT ck_int_score_outcome CHECK (outcome NOT IN ('PASS','FAIL') OR score IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 9. referral
--    An internal recommendation, 1:1 with the application it produced.
--    Storing application_id only (instead of repeating job_id and
--    candidate_id) removes the transitive dependency that would otherwise
--    break 3NF; referrer_id stays because it is not determined by the
--    application.
-- ---------------------------------------------------------------------
CREATE TABLE referral (
  referral_id    INT          NOT NULL AUTO_INCREMENT,
  application_id INT          NOT NULL,
  referrer_id    INT          NOT NULL,
  relationship   ENUM('COLLEAGUE','CLASSMATE','FRIEND','FORMER_COLLEAGUE','OTHER') NOT NULL,
  referred_at    DATETIME     NOT NULL,
  bonus_amount   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  bonus_status   ENUM('NONE','PENDING','PAID','FORFEITED') NOT NULL DEFAULT 'NONE',
  PRIMARY KEY (referral_id),
  UNIQUE KEY uk_ref_application (application_id),
  KEY idx_ref_referrer (referrer_id),
  CONSTRAINT fk_ref_app FOREIGN KEY (application_id)
    REFERENCES application (application_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_ref_member FOREIGN KEY (referrer_id)
    REFERENCES member (member_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_ref_bonus CHECK (bonus_amount >= 0)
  -- "referrer <> candidate" and "referrer works at the hiring company"
  -- cannot be expressed as a CHECK (they reach another table), so they
  -- are enforced by trg_referral_validate in 04_views_triggers.sql.
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 10. education
--    1:N from member.  end_year is nullable for a degree in progress.
-- ---------------------------------------------------------------------
CREATE TABLE education (
  education_id  INT          NOT NULL AUTO_INCREMENT,
  member_id     INT          NOT NULL,
  school_name   VARCHAR(100) NOT NULL,
  degree        ENUM('ASSOCIATE','DIPLOMA','BACHELOR','MASTER','MBA','PHD') NOT NULL,
  field_of_study VARCHAR(80) NOT NULL,
  start_year    SMALLINT     NOT NULL,
  end_year      SMALLINT     NULL,
  PRIMARY KEY (education_id),
  KEY idx_edu_member (member_id),
  CONSTRAINT fk_edu_member FOREIGN KEY (member_id)
    REFERENCES member (member_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ck_edu_years CHECK (start_year BETWEEN 1950 AND 2026
                                 AND (end_year IS NULL OR (end_year >= start_year AND end_year <= 2030)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 11. experience
--     1:N from member to company, carrying title and period.  A member
--     has at most one current position: the stored generated column
--     current_member_id is member_id when is_current = 1 and NULL
--     otherwise, and a UNIQUE key over it permits many NULLs but only
--     one live row per member.  MySQL 8.0 has no partial indexes, so this
--     is the portable substitute for "UNIQUE ... WHERE is_current = 1".
-- ---------------------------------------------------------------------
CREATE TABLE experience (
  experience_id  INT          NOT NULL AUTO_INCREMENT,
  member_id      INT          NOT NULL,
  company_id     INT          NOT NULL,
  title          VARCHAR(100) NOT NULL,
  start_date     DATE         NOT NULL,
  end_date       DATE         NULL,
  is_current     TINYINT(1)   NOT NULL DEFAULT 0,
  current_member_id INT GENERATED ALWAYS AS (IF(is_current = 1, member_id, NULL)) VIRTUAL,
  PRIMARY KEY (experience_id),
  UNIQUE KEY uk_exp_one_current (current_member_id),
  KEY idx_exp_member (member_id, is_current),
  KEY idx_exp_company (company_id, is_current),
  CONSTRAINT fk_exp_member FOREIGN KEY (member_id)
    REFERENCES member (member_id) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT fk_exp_company FOREIGN KEY (company_id)
    REFERENCES company (company_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ck_exp_current CHECK (is_current IN (0,1)),
  CONSTRAINT ck_exp_dates CHECK (end_date IS NULL OR end_date >= start_date),
  CONSTRAINT ck_exp_current_open CHECK ((is_current = 1 AND end_date IS NULL)
                                     OR (is_current = 0 AND end_date IS NOT NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 12. connection
--     Undirected social edge.  The pair is stored once, in canonical
--     order (member_a_id < member_b_id), so (a,b) and (b,a) cannot both
--     exist; the CHECK is the constraint, not a convention.
--     This is the table the recursive CTE in Q18 walks.
-- ---------------------------------------------------------------------
CREATE TABLE connection (
  member_a_id  INT          NOT NULL,
  member_b_id  INT          NOT NULL,
  connected_at DATETIME     NOT NULL,
  connection_type ENUM('COLLEAGUE','CLASSMATE','FRIEND','FOLLOW') NOT NULL DEFAULT 'COLLEAGUE',
  PRIMARY KEY (member_a_id, member_b_id),
  KEY idx_conn_b (member_b_id),
  CONSTRAINT fk_conn_a FOREIGN KEY (member_a_id)
    REFERENCES member (member_id) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT fk_conn_b FOREIGN KEY (member_b_id)
    REFERENCES member (member_id) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT ck_conn_order CHECK (member_a_id < member_b_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- End of schema.  Twelve tables, 11 entity sets + connection as the one
-- self-referencing relationship set materialised as a table.
-- ---------------------------------------------------------------------
