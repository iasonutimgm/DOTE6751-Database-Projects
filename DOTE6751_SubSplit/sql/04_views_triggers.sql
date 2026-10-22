-- =====================================================================
-- SubSplit | 04_views_triggers.sql
-- Views (read models) and triggers (integrity rules MySQL cannot express
-- declaratively). Run AFTER 01_schema.sql.
-- =====================================================================
USE subsplit_db;
SET NAMES utf8mb4;

DROP VIEW  IF EXISTS v_group_overview;
DROP VIEW  IF EXISTS v_escrow_balance;
DROP TRIGGER IF EXISTS trg_password_log;
DROP TRIGGER IF EXISTS trg_seat_capacity;
DROP TRIGGER IF EXISTS trg_default_payment_ins;
DROP TRIGGER IF EXISTS trg_default_payment_upd;
DROP TRIGGER IF EXISTS trg_escrow_after_payout;

-- ---------------------------------------------------------------------
-- View 1: one line per group, with occupancy and fill time.
-- ---------------------------------------------------------------------
CREATE VIEW v_group_overview AS
SELECT
  g.group_id,
  g.status,
  ds.brand,
  ds.region,
  ds.max_seats,
  g.seat_price,
  ds.official_monthly_price,
  ROUND(g.seat_price / ds.official_monthly_price * 100, 1) AS price_pct_of_official,
  u.display_name                                          AS host_name,
  u.credit_score                                          AS host_credit,
  COUNT(s.seat_id)                                        AS seats_taken,
  ds.max_seats - COUNT(s.seat_id)                         AS seats_left,
  g.created_at,
  g.full_at,
  TIMESTAMPDIFF(HOUR, g.created_at, g.full_at)            AS hours_to_fill
FROM carpool_group g
JOIN digital_service ds ON ds.service_id = g.service_id
JOIN app_user       u  ON u.user_id      = g.host_id
LEFT JOIN membership_seat s
       ON s.group_id = g.group_id
      AND s.seat_status IN ('ACTIVE','LEAVING')
GROUP BY g.group_id, g.status, ds.brand, ds.region, ds.max_seats,
         g.seat_price, ds.official_monthly_price, u.display_name,
         u.credit_score, g.created_at, g.full_at;

-- ---------------------------------------------------------------------
-- View 2: escrow balance reconciled against its own ledger.
-- ---------------------------------------------------------------------
CREATE VIEW v_escrow_balance AS
SELECT
  e.escrow_id,
  e.seat_id,
  e.escrow_status,
  e.total_prepaid,
  e.released_amount,
  e.remaining_amount,
  COALESCE(SUM(p.amount), 0)                              AS ledger_released,
  e.released_amount - COALESCE(SUM(p.amount), 0)           AS drift,
  COUNT(p.payout_id)                                      AS payouts
FROM escrow_payment e
LEFT JOIN monthly_payout_log p
       ON p.escrow_id = e.escrow_id
      AND p.payout_status = 'SETTLED'
GROUP BY e.escrow_id, e.seat_id, e.escrow_status, e.total_prepaid,
         e.released_amount, e.remaining_amount;

-- ---------------------------------------------------------------------
-- Trigger 1: any credential change is journalled automatically.
-- ---------------------------------------------------------------------
DELIMITER $$
CREATE TRIGGER trg_password_log
AFTER UPDATE ON credential_vault
FOR EACH ROW
BEGIN
  IF NOT (NEW.password_updated_at <=> OLD.password_updated_at) THEN
    INSERT INTO password_change_log (group_id, changed_at, changed_by, reason)
    VALUES (NEW.group_id, NEW.password_updated_at, NEW.updated_by, 'ROUTINE');
  END IF;
END$$

-- ---------------------------------------------------------------------
-- Trigger 2: a seat cannot be sold beyond the product's seat ceiling,
-- and not while the group is frozen or closed.
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_seat_capacity
BEFORE INSERT ON membership_seat
FOR EACH ROW
BEGIN
  DECLARE v_max   TINYINT;
  DECLARE v_taken INT;
  DECLARE v_status VARCHAR(16);

  SELECT ds.max_seats, g.status
    INTO v_max, v_status
    FROM carpool_group g
    JOIN digital_service ds ON ds.service_id = g.service_id
   WHERE g.group_id = NEW.group_id;

  IF v_status IN ('FROZEN','CLOSED') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'group is not open for new seats';
  END IF;

  SELECT COUNT(*) INTO v_taken
    FROM membership_seat
   WHERE group_id = NEW.group_id
     AND seat_status IN ('ACTIVE','LEAVING');

  IF v_taken >= v_max THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'seat capacity exceeded for this service';
  END IF;
END$$

-- ---------------------------------------------------------------------
-- Trigger 3: only one default payment instrument per user.
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_default_payment_ins
BEFORE INSERT ON payment_method
FOR EACH ROW
BEGIN
  IF NEW.is_default = 1 THEN
    UPDATE payment_method SET is_default = 0 WHERE user_id = NEW.user_id;
  END IF;
END$$

CREATE TRIGGER trg_default_payment_upd
BEFORE UPDATE ON payment_method
FOR EACH ROW
BEGIN
  IF NEW.is_default = 1 AND OLD.is_default = 0 THEN
    UPDATE payment_method SET is_default = 0
     WHERE user_id = NEW.user_id AND pm_id <> NEW.pm_id;
  END IF;
END$$

-- ---------------------------------------------------------------------
-- Trigger 4: the ledger is the source of truth for the escrow balance.
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_escrow_after_payout
AFTER INSERT ON monthly_payout_log
FOR EACH ROW
BEGIN
  DECLARE v_released DECIMAL(10,2);

  IF NEW.payout_status = 'SETTLED' THEN
    SELECT released_amount + NEW.amount INTO v_released
      FROM escrow_payment WHERE escrow_id = NEW.escrow_id;

    UPDATE escrow_payment
       SET released_amount  = v_released,
           remaining_amount = total_prepaid - v_released,
           escrow_status    = CASE WHEN total_prepaid - v_released <= 0
                                   THEN 'RELEASED' ELSE 'PARTIAL' END
     WHERE escrow_id = NEW.escrow_id;
  END IF;
END$$
DELIMITER ;

SELECT 'objects' AS kind,
       (SELECT COUNT(*) FROM information_schema.views
        WHERE table_schema='subsplit_db') AS views_created,
       (SELECT COUNT(*) FROM information_schema.triggers
        WHERE trigger_schema='subsplit_db') AS triggers_created;
