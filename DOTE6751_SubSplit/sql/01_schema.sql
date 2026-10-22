-- =====================================================================
-- SubSplit : escrow-protected subscription sharing platform
-- 01_schema.sql  |  MySQL 8.0  |  utf8mb4
-- DOTE 6751 Group Project
--
-- Run order: 01_schema -> 02_seed -> 03_queries -> 04_views_triggers
-- =====================================================================

DROP DATABASE IF EXISTS subsplit_db;
CREATE DATABASE subsplit_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE subsplit_db;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------------------
-- 1. app_user
--    Every natural person on the platform. A user may act as a host
--    (owns a group) and as a member (sits in someone else's group);
--    the role column only separates ordinary users from administrators.
-- ---------------------------------------------------------------------
CREATE TABLE app_user (
  user_id       INT           NOT NULL AUTO_INCREMENT,
  display_name  VARCHAR(80)   NOT NULL,
  account_role  ENUM('USER','ADMIN') NOT NULL DEFAULT 'USER',
  occupation    ENUM('STUDENT','PROFESSIONAL','OTHER') NOT NULL DEFAULT 'OTHER',
  school        VARCHAR(80)   NULL,
  credit_score  TINYINT UNSIGNED NOT NULL DEFAULT 100,
  status        ENUM('ACTIVE','SUSPENDED','CLOSED') NOT NULL DEFAULT 'ACTIVE',
  joined_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  KEY idx_user_role (account_role),
  CONSTRAINT ck_user_credit CHECK (credit_score BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 2. payment_method
--    A user may bind several instruments (1:N). Exactly one of them is
--    the default; the uniqueness of that default is enforced by trigger
--    trg_default_payment because MySQL cannot express a partial index.
-- ---------------------------------------------------------------------
CREATE TABLE payment_method (
  pm_id          INT          NOT NULL AUTO_INCREMENT,
  user_id        INT          NOT NULL,
  method_type    ENUM('CARD','ALIPAY','WECHAT','BANK') NOT NULL,
  masked_account VARCHAR(40)  NOT NULL,
  is_default     TINYINT(1)   NOT NULL DEFAULT 0,
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (pm_id),
  UNIQUE KEY uk_pm_user_account (user_id, masked_account),
  KEY idx_pm_user (user_id),
  CONSTRAINT fk_pm_user FOREIGN KEY (user_id)
    REFERENCES app_user (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ck_pm_default CHECK (is_default IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 3. digital_service
--    The dictionary of subscription products. The seat ceiling lives
--    here and nowhere else: a group's capacity is a property of the
--    product, not of the group (3NF: no transitive dependency).
-- ---------------------------------------------------------------------
CREATE TABLE digital_service (
  service_id            INT           NOT NULL AUTO_INCREMENT,
  brand                 VARCHAR(60)   NOT NULL,
  region                ENUM('HK','US','CN','JP','UK','SG') NOT NULL,
  plan_name             VARCHAR(60)   NOT NULL DEFAULT 'Family',
  max_seats             TINYINT UNSIGNED NOT NULL DEFAULT 6,
  official_monthly_price DECIMAL(8,2) NOT NULL,
  currency              CHAR(3)       NOT NULL DEFAULT 'HKD',
  PRIMARY KEY (service_id),
  UNIQUE KEY uk_service (brand, region, plan_name),
  CONSTRAINT ck_service_seats CHECK (max_seats BETWEEN 2 AND 6),
  CONSTRAINT ck_service_price CHECK (official_monthly_price > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 4. carpool_group
--    The central entity: one host resells seats of one subscription.
--    full_at records the moment the last seat was taken, which is what
--    makes "average time to fill" answerable (a derived-state column).
-- ---------------------------------------------------------------------
CREATE TABLE carpool_group (
  group_id    INT           NOT NULL AUTO_INCREMENT,
  host_id     INT           NOT NULL,
  service_id  INT           NOT NULL,
  status      ENUM('RECRUITING','FULL','ACTIVE','FROZEN','CLOSED')
                            NOT NULL DEFAULT 'RECRUITING',
  seat_price  DECIMAL(8,2)  NOT NULL,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  full_at     DATETIME      NULL,
  closed_at   DATETIME      NULL,
  PRIMARY KEY (group_id),
  KEY idx_group_service_status (service_id, status),
  KEY idx_group_host (host_id),
  CONSTRAINT fk_group_host FOREIGN KEY (host_id)
    REFERENCES app_user (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_group_service FOREIGN KEY (service_id)
    REFERENCES digital_service (service_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_group_price CHECK (seat_price > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 5. credential_vault  (weak entity, 1:1 with carpool_group)
--    Its identity is borrowed from the group, hence group_id is both PK
--    and FK. Holds the invite link and the (encrypted) household pass-
--    phrase, plus the timestamp the risk query watches.
-- ---------------------------------------------------------------------
CREATE TABLE credential_vault (
  group_id            INT           NOT NULL,
  invite_url          VARCHAR(255)  NOT NULL,
  encrypted_passphrase VARCHAR(255) NOT NULL,
  password_updated_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  verified_at         DATETIME      NULL,
  updated_by          INT           NULL,
  PRIMARY KEY (group_id),
  CONSTRAINT fk_vault_group FOREIGN KEY (group_id)
    REFERENCES carpool_group (group_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_vault_user FOREIGN KEY (updated_by)
    REFERENCES app_user (user_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 6. membership_seat  (associative entity for the M:N host-guest link)
--    A seat is not a pure bridge: it carries its own state and its own
--    twelve-month window, so it is modelled as an entity.
-- ---------------------------------------------------------------------
CREATE TABLE membership_seat (
  seat_id      INT          NOT NULL AUTO_INCREMENT,
  group_id     INT          NOT NULL,
  member_id    INT          NOT NULL,
  joined_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at   DATETIME     NOT NULL,
  seat_status  ENUM('ACTIVE','LEAVING','LEFT','REFUNDED') NOT NULL DEFAULT 'ACTIVE',
  PRIMARY KEY (seat_id),
  UNIQUE KEY uk_seat_group_member (group_id, member_id),
  KEY idx_seat_group (group_id, seat_status),
  KEY idx_seat_member (member_id, seat_status),
  CONSTRAINT fk_seat_group FOREIGN KEY (group_id)
    REFERENCES carpool_group (group_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_seat_member FOREIGN KEY (member_id)
    REFERENCES app_user (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_seat_window CHECK (expires_at > joined_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 7. escrow_payment  (1:1 with a seat)
--    released_amount and remaining_amount are maintained by trigger
--    trg_escrow_after_payout. Both are stored deliberately (see
--    Design_Rationale): the balance is read on every page view, while
--    the ledger is written once a month.
-- ---------------------------------------------------------------------
CREATE TABLE escrow_payment (
  escrow_id        INT           NOT NULL AUTO_INCREMENT,
  seat_id          INT           NOT NULL,
  total_prepaid    DECIMAL(10,2) NOT NULL,
  released_amount  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  remaining_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  escrow_status    ENUM('HELD','PARTIAL','RELEASED','FROZEN','REFUNDED')
                                 NOT NULL DEFAULT 'HELD',
  created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (escrow_id),
  UNIQUE KEY uk_escrow_seat (seat_id),
  KEY idx_escrow_status (escrow_status),
  CONSTRAINT fk_escrow_seat FOREIGN KEY (seat_id)
    REFERENCES membership_seat (seat_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ck_escrow_positive CHECK (total_prepaid > 0),
  CONSTRAINT ck_escrow_balance CHECK (
    released_amount >= 0
    AND released_amount <= total_prepaid
    AND remaining_amount = total_prepaid - released_amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 8. monthly_payout_log
--    The ledger: one row per escrow per month. (escrow_id, release_month)
--    is unique, so a month can never be paid twice.
-- ---------------------------------------------------------------------
CREATE TABLE monthly_payout_log (
  payout_id     INT           NOT NULL AUTO_INCREMENT,
  escrow_id     INT           NOT NULL,
  release_month DATE          NOT NULL,
  amount        DECIMAL(10,2) NOT NULL,
  platform_fee  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  payout_status ENUM('SETTLED','BLOCKED','REVERSED') NOT NULL DEFAULT 'SETTLED',
  settled_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (payout_id),
  UNIQUE KEY uk_payout_escrow_month (escrow_id, release_month),
  KEY idx_payout_month (release_month),
  CONSTRAINT fk_payout_escrow FOREIGN KEY (escrow_id)
    REFERENCES escrow_payment (escrow_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ck_payout_amount CHECK (amount > 0),
  CONSTRAINT ck_payout_fee CHECK (platform_fee >= 0 AND platform_fee < amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 9. password_change_log
--    Append-only history of credential changes. The vault only knows
--    the latest timestamp; the risk query needs the count in a window.
-- ---------------------------------------------------------------------
CREATE TABLE password_change_log (
  log_id      INT         NOT NULL AUTO_INCREMENT,
  group_id    INT         NOT NULL,
  changed_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  changed_by  INT         NULL,
  reason      ENUM('ROUTINE','SUSPICIOUS','RESET') NOT NULL DEFAULT 'ROUTINE',
  PRIMARY KEY (log_id),
  KEY idx_pwd_group_time (group_id, changed_at),
  CONSTRAINT fk_pwd_group FOREIGN KEY (group_id)
    REFERENCES credential_vault (group_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_pwd_user FOREIGN KEY (changed_by)
    REFERENCES app_user (user_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 10. dispute
--     The complaint state machine. Money only moves after an admin
--     moves the row to REFUNDED; the escrow freezes while it is open.
-- ---------------------------------------------------------------------
CREATE TABLE dispute (
  dispute_id     INT          NOT NULL AUTO_INCREMENT,
  seat_id        INT          NOT NULL,
  category       ENUM('NO_ACCESS','PASSWORD_CHANGED','KICKED_OUT','OTHER') NOT NULL,
  detail         VARCHAR(500) NULL,
  dispute_status ENUM('OPEN','UNDER_REVIEW','REFUNDED','REJECTED') NOT NULL DEFAULT 'OPEN',
  opened_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at    DATETIME     NULL,
  reviewer_id    INT          NULL,
  resolution_note VARCHAR(255) NULL,
  PRIMARY KEY (dispute_id),
  KEY idx_dispute_seat (seat_id),
  KEY idx_dispute_status_time (dispute_status, opened_at),
  CONSTRAINT fk_dispute_seat FOREIGN KEY (seat_id)
    REFERENCES membership_seat (seat_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_dispute_reviewer FOREIGN KEY (reviewer_id)
    REFERENCES app_user (user_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 11. credit_event
--     Every change to app_user.credit_score leaves a row here, so the
--     score is auditable and can be recomputed from first principles.
-- ---------------------------------------------------------------------
CREATE TABLE credit_event (
  event_id      INT      NOT NULL AUTO_INCREMENT,
  user_id       INT      NOT NULL,
  delta         SMALLINT NOT NULL,
  reason        ENUM('DISPUTE_LOST','LATE_RELEASE','GOOD_STANDING','MANUAL','PENALTY') NOT NULL,
  ref_dispute_id INT     NULL,
  score_after   TINYINT UNSIGNED NOT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (event_id),
  KEY idx_credit_user_time (user_id, created_at),
  CONSTRAINT fk_credit_user FOREIGN KEY (user_id)
    REFERENCES app_user (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_credit_dispute FOREIGN KEY (ref_dispute_id)
    REFERENCES dispute (dispute_id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT ck_credit_delta CHECK (delta BETWEEN -100 AND 100),
  CONSTRAINT ck_credit_after CHECK (score_after BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'schema created' AS status,
       (SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'subsplit_db' AND table_type = 'BASE TABLE') AS tables_created;
