-- =====================================================================
-- SubSplit | 05_transactions.sql
-- Transactional episodes. Everything here is rolled back on purpose, so
-- running the file leaves the database exactly as it was.
-- =====================================================================
USE subsplit_db;
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------
-- D1. A complaint is filed and the money is frozen, atomically.
--     Either the dispute row and the frozen balance both exist, or neither.
-- ---------------------------------------------------------------------
SELECT 'D1 before' AS step, e.escrow_id, e.escrow_status, e.remaining_amount
FROM escrow_payment e
WHERE e.escrow_id = 1;

START TRANSACTION;

INSERT INTO dispute (seat_id, category, detail, dispute_status)
SELECT seat_id, 'NO_ACCESS', 'member cannot sign in after a password change', 'OPEN'
FROM escrow_payment WHERE escrow_id = 1;

UPDATE escrow_payment
   SET escrow_status = 'FROZEN'
 WHERE escrow_id = 1;

SELECT 'D1 inside transaction' AS step,
       (SELECT COUNT(*) FROM dispute
         WHERE seat_id = (SELECT seat_id FROM escrow_payment WHERE escrow_id = 1)) AS disputes_on_seat,
       (SELECT escrow_status FROM escrow_payment WHERE escrow_id = 1) AS status;

ROLLBACK;

SELECT 'D1 after rollback' AS step,
       (SELECT COUNT(*) FROM dispute
         WHERE seat_id = (SELECT seat_id FROM escrow_payment WHERE escrow_id = 1)) AS disputes_on_seat,
       (SELECT escrow_status FROM escrow_payment WHERE escrow_id = 1) AS status;

-- ---------------------------------------------------------------------
-- D2. A release that would overdraw the escrow is refused by the engine.
--     Run the two statements below by hand to see the failure:
--
--     UPDATE escrow_payment SET remaining_amount = 0.01 WHERE escrow_id = 1;
--       -> ERROR 3819: Check constraint 'ck_escrow_balance' is violated
--
--     INSERT INTO monthly_payout_log (escrow_id, release_month, amount, platform_fee)
--     VALUES (1, '2030-01-01', 9999.00, 0.00);
--       -> ERROR 3819 as well, because the trigger would move the balance
--          below zero and the CHECK refuses the resulting row.
--
--     Both are left commented out so that this file can be executed end
--     to end; the verification guide asks the reader to try them.
-- ---------------------------------------------------------------------

-- ---------------------------------------------------------------------
-- D3. The capacity rule survives a hand-written INSERT from any client.
--     A group already at its ceiling refuses a new seat:
--
--     INSERT INTO membership_seat (group_id, member_id, joined_at, expires_at)
--     VALUES (1, 2, NOW(), NOW() + INTERVAL 1 YEAR);
--       -> ERROR 1644: seat capacity exceeded for this service
--
--     Kept commented out for the same reason as D2.
-- ---------------------------------------------------------------------

-- ---------------------------------------------------------------------
-- D4. A full release cycle inside one transaction: a month is paid, the
--     balance moves, the ledger grows. The episode is rolled back, so the
--     reader can re-run the file as often as they like.
-- ---------------------------------------------------------------------
SET @eid = (SELECT escrow_id FROM escrow_payment
             WHERE escrow_status = 'HELD' ORDER BY escrow_id LIMIT 1);
SET @amt = (SELECT ROUND(total_prepaid / 12, 2) FROM escrow_payment WHERE escrow_id = @eid);
SET @fee = ROUND(@amt * 0.05, 2);

SELECT 'D4 before' AS step, escrow_id, released_amount, remaining_amount, escrow_status
FROM escrow_payment WHERE escrow_id = @eid;

START TRANSACTION;

UPDATE escrow_payment SET escrow_status = 'PARTIAL' WHERE escrow_id = @eid;

INSERT INTO monthly_payout_log (escrow_id, release_month, amount, platform_fee, payout_status)
VALUES (@eid, '2030-01-01', @amt, @fee, 'SETTLED');

SELECT 'D4 inside transaction' AS step, escrow_id, released_amount, remaining_amount,
       escrow_status
FROM escrow_payment WHERE escrow_id = @eid;

ROLLBACK;

SELECT 'D4 after rollback' AS step, escrow_id, released_amount, remaining_amount,
       escrow_status
FROM escrow_payment WHERE escrow_id = @eid;
