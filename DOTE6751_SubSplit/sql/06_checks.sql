-- =====================================================================
-- SubSplit | 06_checks.sql
-- Twelve acceptance checks. Every row should read PASS; a single FAIL is
-- a defect, not a warning. Designed to be run after 01+02+04.
-- =====================================================================
USE subsplit_db;
SET NAMES utf8mb4;

SELECT 'C01 tables present' AS check_name,
       (SELECT COUNT(*) FROM information_schema.tables
         WHERE table_schema = 'subsplit_db' AND table_type = 'BASE TABLE') AS found,
       11 AS expected,
       IF((SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'subsplit_db' AND table_type = 'BASE TABLE') = 11, 'PASS', 'FAIL') AS status
UNION ALL
SELECT 'C02 views and triggers present',
       (SELECT COUNT(*) FROM information_schema.views WHERE table_schema='subsplit_db')
     + (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='subsplit_db'),
       7,
       IF((SELECT COUNT(*) FROM information_schema.views WHERE table_schema='subsplit_db')
        + (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='subsplit_db') = 7, 'PASS', 'FAIL')
UNION ALL
SELECT 'C03 no group above its seat ceiling',
       (SELECT COUNT(*) FROM v_group_overview WHERE seats_taken > max_seats), 0,
       IF((SELECT COUNT(*) FROM v_group_overview WHERE seats_taken > max_seats) = 0, 'PASS', 'FAIL')
UNION ALL
SELECT 'C04 escrow balance identity holds',
       (SELECT COUNT(*) FROM escrow_payment
         WHERE remaining_amount <> total_prepaid - released_amount), 0,
       IF((SELECT COUNT(*) FROM escrow_payment
            WHERE remaining_amount <> total_prepaid - released_amount) = 0, 'PASS', 'FAIL')
UNION ALL
SELECT 'C05 balance equals its ledger',
       (SELECT COUNT(*) FROM v_escrow_balance WHERE ABS(drift) > 0.001), 0,
       IF((SELECT COUNT(*) FROM v_escrow_balance WHERE ABS(drift) > 0.001) = 0, 'PASS', 'FAIL')
UNION ALL
SELECT 'C06 no escrow paid more than 12 times',
       (SELECT COUNT(*) FROM (SELECT escrow_id FROM monthly_payout_log
                               GROUP BY escrow_id HAVING COUNT(*) > 12) t), 0,
       IF((SELECT COUNT(*) FROM (SELECT escrow_id FROM monthly_payout_log
                                  GROUP BY escrow_id HAVING COUNT(*) > 12) t) = 0, 'PASS', 'FAIL')
UNION ALL
SELECT 'C07 no month paid twice',
       (SELECT COUNT(*) FROM (SELECT escrow_id, release_month FROM monthly_payout_log
                               GROUP BY escrow_id, release_month HAVING COUNT(*) > 1) t), 0,
       IF((SELECT COUNT(*) FROM (SELECT escrow_id, release_month FROM monthly_payout_log
                                  GROUP BY escrow_id, release_month HAVING COUNT(*) > 1) t) = 0, 'PASS', 'FAIL')
UNION ALL
SELECT 'C08 one default instrument per user',
       (SELECT COUNT(*) FROM (SELECT user_id FROM payment_method
                               WHERE is_default = 1
                               GROUP BY user_id HAVING COUNT(*) > 1) t), 0,
       IF((SELECT COUNT(*) FROM (SELECT user_id FROM payment_method
                                  WHERE is_default = 1
                                  GROUP BY user_id HAVING COUNT(*) > 1) t) = 0, 'PASS', 'FAIL')
UNION ALL
SELECT 'C09 credit score matches its audit trail',
       (SELECT COUNT(*) FROM app_user u
         WHERE u.credit_score <> LEAST(100, GREATEST(0,
               COALESCE((SELECT SUM(delta) FROM credit_event c WHERE c.user_id = u.user_id), 0) + 100))), 0,
       IF((SELECT COUNT(*) FROM app_user u
            WHERE u.credit_score <> LEAST(100, GREATEST(0,
                  COALESCE((SELECT SUM(delta) FROM credit_event c WHERE c.user_id = u.user_id), 0) + 100))) = 0, 'PASS', 'FAIL')
UNION ALL
SELECT 'C10 every seat ends after it starts',
       (SELECT COUNT(*) FROM membership_seat WHERE expires_at <= joined_at), 0,
       IF((SELECT COUNT(*) FROM membership_seat WHERE expires_at <= joined_at) = 0, 'PASS', 'FAIL')
UNION ALL
SELECT 'C11 reviewed disputes have a reviewer',
       (SELECT COUNT(*) FROM dispute
         WHERE dispute_status IN ('UNDER_REVIEW','REFUNDED','REJECTED')
           AND reviewer_id IS NULL), 0,
       IF((SELECT COUNT(*) FROM dispute
            WHERE dispute_status IN ('UNDER_REVIEW','REFUNDED','REJECTED')
              AND reviewer_id IS NULL) = 0, 'PASS', 'FAIL')
UNION ALL
SELECT 'C12 vault timestamp equals its latest journal entry',
       (SELECT COUNT(*) FROM credential_vault v
         WHERE EXISTS (SELECT 1 FROM password_change_log l WHERE l.group_id = v.group_id)
           AND v.password_updated_at <> (SELECT MAX(l.changed_at) FROM password_change_log l
                                          WHERE l.group_id = v.group_id)), 0,
       IF((SELECT COUNT(*) FROM credential_vault v
            WHERE EXISTS (SELECT 1 FROM password_change_log l WHERE l.group_id = v.group_id)
              AND v.password_updated_at <> (SELECT MAX(l.changed_at) FROM password_change_log l
                                             WHERE l.group_id = v.group_id)) = 0, 'PASS', 'FAIL');
