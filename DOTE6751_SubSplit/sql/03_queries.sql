-- =====================================================================
-- SubSplit | 03_queries.sql
-- 18 analytical queries, grouped by difficulty.
-- Every statement is standalone: select it in Navicat and press Ctrl+R.
-- Requires 01_schema.sql + 02_seed.sql + 04_views_triggers.sql.
-- =====================================================================
USE subsplit_db;
SET NAMES utf8mb4;

-- @query Q01 | Precise seat hunting: recruiting Spotify-HK groups, exactly one seat left, trustworthy host
-- technique: LEFT JOIN + aggregate + HAVING on a computed alias
SELECT g.group_id,
       ds.brand,
       ds.region,
       g.seat_price,
       u.display_name                       AS host_name,
       u.credit_score                       AS host_credit,
       COUNT(s.seat_id)                     AS seats_taken,
       ds.max_seats,
       ds.max_seats - COUNT(s.seat_id)      AS seats_left
FROM carpool_group g
JOIN digital_service ds ON ds.service_id = g.service_id
JOIN app_user        u  ON u.user_id     = g.host_id
LEFT JOIN membership_seat s
       ON s.group_id = g.group_id
      AND s.seat_status IN ('ACTIVE','LEAVING')
WHERE g.status = 'RECRUITING'
  AND ds.brand = 'Spotify'
  AND ds.region = 'HK'
  AND u.credit_score = 100
GROUP BY g.group_id, ds.brand, ds.region, g.seat_price,
         u.display_name, u.credit_score, ds.max_seats
HAVING seats_left = 1
ORDER BY g.seat_price, g.group_id;

-- @query Q02 | Which five services do students actually occupy?
-- technique: multi-join + aggregate + ORDER BY / LIMIT
SELECT ds.brand,
       ds.region,
       COUNT(s.seat_id)             AS student_seats,
       COUNT(DISTINCT g.group_id)   AS group_count
FROM membership_seat s
JOIN app_user       u  ON u.user_id    = s.member_id AND u.occupation = 'STUDENT'
JOIN carpool_group  g  ON g.group_id   = s.group_id
JOIN digital_service ds ON ds.service_id = g.service_id
WHERE s.seat_status IN ('ACTIVE','LEAVING')
GROUP BY ds.brand, ds.region
ORDER BY student_seats DESC, ds.brand
LIMIT 5;

-- @query Q03 | How long does it take to fill a group, by service?
-- technique: TIMESTAMPDIFF + AVG/MIN/MAX over a filtered set
SELECT ds.brand,
       ds.region,
       COUNT(*)                                                        AS groups_filled,
       ROUND(AVG(TIMESTAMPDIFF(HOUR, g.created_at, g.full_at)), 1)     AS avg_hours,
       MIN(TIMESTAMPDIFF(HOUR, g.created_at, g.full_at))               AS fastest_hours,
       MAX(TIMESTAMPDIFF(HOUR, g.created_at, g.full_at))               AS slowest_hours
FROM carpool_group g
JOIN digital_service ds ON ds.service_id = g.service_id
WHERE g.full_at IS NOT NULL
GROUP BY ds.brand, ds.region
ORDER BY avg_hours DESC;

-- @query Q04 | Platform revenue: monthly recurring revenue (MRR) from the 5% fee
-- technique: DATE_FORMAT bucketing + SUM
SELECT DATE_FORMAT(p.release_month, '%Y-%m') AS ym,
       COUNT(*)                              AS payouts,
       ROUND(SUM(p.amount), 2)               AS gross_released,
       ROUND(SUM(p.platform_fee), 2)         AS platform_revenue
FROM monthly_payout_log p
WHERE p.payout_status = 'SETTLED'
GROUP BY DATE_FORMAT(p.release_month, '%Y-%m')
ORDER BY ym;

-- @query Q05 | Risk control: groups that changed the passphrase >= 3 times in 30 days AND drew >= 2 "cannot log in" complaints
-- technique: correlated scalar subqueries + HAVING
SELECT g.group_id,
       u.display_name AS host_name,
       ds.brand,
       ds.region,
       g.status,
       u.credit_score,
       (SELECT COUNT(*)
          FROM password_change_log l
         WHERE l.group_id = g.group_id
           AND l.changed_at >= NOW() - INTERVAL 30 DAY)                        AS password_changes_30d,
       (SELECT COUNT(*)
          FROM dispute d
          JOIN membership_seat s2 ON s2.seat_id = d.seat_id
         WHERE s2.group_id = g.group_id
           AND d.category = 'NO_ACCESS'
           AND d.opened_at >= NOW() - INTERVAL 30 DAY)                        AS no_access_complaints_30d
FROM carpool_group g
JOIN app_user        u  ON u.user_id     = g.host_id
JOIN digital_service ds ON ds.service_id = g.service_id
HAVING password_changes_30d >= 3
   AND no_access_complaints_30d >= 2
ORDER BY password_changes_30d DESC, no_access_complaints_30d DESC;

-- @query Q06 | One member's footprint: every seat they hold, with money at stake
-- technique: four-way join with a filter on a natural key
SELECT u.display_name,
       ds.brand,
       ds.region,
       g.group_id,
       s.seat_status,
       s.joined_at,
       s.expires_at,
       e.total_prepaid,
       e.remaining_amount,
       e.escrow_status
FROM app_user u
JOIN membership_seat s ON s.member_id = u.user_id
JOIN carpool_group  g  ON g.group_id  = s.group_id
JOIN digital_service ds ON ds.service_id = g.service_id
JOIN escrow_payment e  ON e.seat_id   = s.seat_id
WHERE u.user_id = 42
ORDER BY s.joined_at;

-- @query Q07 | Is the resale price fair? Seat price as a share of the official plan
-- technique: aggregate per service + arithmetic on grouped values
SELECT ds.brand,
       ds.region,
       ds.max_seats,
       ds.official_monthly_price,
       ROUND(AVG(g.seat_price), 2)                                          AS avg_seat_price,
       ROUND(AVG(g.seat_price) * ds.max_seats / ds.official_monthly_price * 100, 1) AS basket_pct_of_official
FROM carpool_group g
JOIN digital_service ds ON ds.service_id = g.service_id
GROUP BY ds.service_id, ds.brand, ds.region, ds.max_seats, ds.official_monthly_price
ORDER BY basket_pct_of_official;

-- @query Q08 | Host leaderboard: who actually earns, after the platform's cut
-- technique: five-way join + SUM over a derived expression
SELECT u.display_name,
       u.credit_score,
       COUNT(DISTINCT g.group_id)              AS groups_hosted,
       ROUND(SUM(p.amount - p.platform_fee), 2) AS net_income
FROM monthly_payout_log p
JOIN escrow_payment  e ON e.escrow_id = p.escrow_id
JOIN membership_seat s ON s.seat_id   = e.seat_id
JOIN carpool_group  g  ON g.group_id  = s.group_id
JOIN app_user        u ON u.user_id   = g.host_id
WHERE p.payout_status = 'SETTLED'
GROUP BY u.user_id, u.display_name, u.credit_score
ORDER BY net_income DESC
LIMIT 10;

-- @query Q09 | Refund rate by service: where do members ask for their money back?
-- technique: COUNT(DISTINCT CASE WHEN ...) to avoid fan-out from multiple complaints
SELECT ds.brand,
       ds.region,
       COUNT(DISTINCT s.seat_id) AS seats,
       COUNT(DISTINCT CASE WHEN d.dispute_status = 'REFUNDED' THEN s.seat_id END) AS refunded_seats,
       ROUND(COUNT(DISTINCT CASE WHEN d.dispute_status = 'REFUNDED' THEN s.seat_id END)
             / COUNT(DISTINCT s.seat_id) * 100, 1) AS refund_rate_pct
FROM membership_seat s
JOIN carpool_group  g  ON g.group_id  = s.group_id
JOIN digital_service ds ON ds.service_id = g.service_id
LEFT JOIN dispute d    ON d.seat_id  = s.seat_id
GROUP BY ds.brand, ds.region
ORDER BY refund_rate_pct DESC;

-- @query Q10 | Two consecutive blocked payouts: a group that stopped paying without being closed
-- technique: window function LAG partitioned by escrow
WITH ledger AS (
  SELECT escrow_id,
         release_month,
         payout_status,
         LAG(payout_status) OVER (PARTITION BY escrow_id ORDER BY release_month) AS prev_status
  FROM monthly_payout_log
)
SELECT escrow_id, release_month
FROM ledger
WHERE payout_status = 'BLOCKED' AND prev_status = 'BLOCKED'
ORDER BY escrow_id, release_month;

-- @query Q11 | Balance audit: stored escrow balance vs the ledger that produced it
-- technique: view over LEFT JOIN + reconciliation ranking
SELECT escrow_id,
       total_prepaid,
       released_amount,
       ledger_released,
       remaining_amount,
       drift
FROM v_escrow_balance
ORDER BY ABS(drift) DESC, escrow_id
LIMIT 10;

-- @query Q12 | How fast do groups fill? Distribution instead of an average
-- technique: derived table + CASE bucketing
SELECT CASE
         WHEN h < 24  THEN '< 1 day'
         WHEN h < 72  THEN '1-3 days'
         WHEN h < 168 THEN '3-7 days'
         ELSE '> 7 days'
       END        AS fill_bucket,
       COUNT(*)   AS group_count
FROM (
  SELECT TIMESTAMPDIFF(HOUR, created_at, full_at) AS h
  FROM carpool_group
  WHERE full_at IS NOT NULL
) t
GROUP BY fill_bucket
ORDER BY MIN(h);

-- @query Q13 | Stale recruiting groups: open for more than 14 days and still short of people
-- technique: business view + date arithmetic
SELECT group_id,
       brand,
       region,
       host_name,
       seats_taken,
       max_seats,
       seats_left,
       DATEDIFF(NOW(), created_at) AS age_days
FROM v_group_overview
WHERE status = 'RECRUITING'
  AND seats_left > 0
  AND created_at < NOW() - INTERVAL 14 DAY
ORDER BY age_days DESC;

-- @query Q14 | Hosts with a damaged credit score who are still recruiting
-- technique: JOIN + predicate on a derived attribute
SELECT u.user_id,
       u.display_name,
       u.credit_score,
       g.group_id,
       ds.brand,
       ds.region,
       g.status
FROM app_user u
JOIN carpool_group  g  ON g.host_id    = u.user_id
JOIN digital_service ds ON ds.service_id = g.service_id
WHERE u.credit_score < 60
  AND g.status = 'RECRUITING'
ORDER BY u.credit_score;

-- @query Q15 | Occupancy check: groups at or over their seat ceiling
-- technique: aggregate view + filter on a computed column
SELECT group_id, brand, region, status, seats_taken, max_seats, seats_left
FROM v_group_overview
WHERE seats_taken >= max_seats
ORDER BY group_id
LIMIT 12;

-- @query Q16 | Complaint mix in the last 30 days, with handling time
-- technique: conditional aggregation + COALESCE for unresolved rows
SELECT d.category,
       d.dispute_status,
       COUNT(*)                                                              AS complaints,
       ROUND(AVG(TIMESTAMPDIFF(HOUR, d.opened_at, COALESCE(d.reviewed_at, NOW()))), 1) AS avg_hours_to_close
FROM dispute d
WHERE d.opened_at >= NOW() - INTERVAL 30 DAY
GROUP BY d.category, d.dispute_status
ORDER BY d.category, complaints DESC;

-- @query Q17 | Month-over-month change in platform fee income
-- technique: CTE + LAG over an aggregated month series
WITH monthly AS (
  SELECT release_month,
         SUM(platform_fee) AS fee
  FROM monthly_payout_log
  WHERE payout_status = 'SETTLED'
  GROUP BY release_month
)
SELECT release_month,
       ROUND(fee, 2) AS platform_fee,
       ROUND(LAG(fee) OVER (ORDER BY release_month), 2) AS prev_month_fee,
       ROUND((fee - LAG(fee) OVER (ORDER BY release_month))
             / LAG(fee) OVER (ORDER BY release_month) * 100, 1) AS mom_pct
FROM monthly
ORDER BY release_month;

-- @query Q18 | Recommendation slot: other recruiting groups on the services this member already pays for
-- technique: IN-subquery + NOT EXISTS anti-join
SELECT v.brand,
       v.region,
       v.group_id,
       v.seat_price,
       v.seats_left,
       v.host_name,
       v.host_credit
FROM v_group_overview v
WHERE v.status = 'RECRUITING'
  AND v.seats_left > 0
  AND v.brand IN (
        SELECT ds2.brand
        FROM membership_seat s2
        JOIN carpool_group  g2  ON g2.group_id   = s2.group_id
        JOIN digital_service ds2 ON ds2.service_id = g2.service_id
        JOIN app_user        u2  ON u2.user_id   = s2.member_id
        WHERE u2.user_id = 42)
  AND NOT EXISTS (
        SELECT 1
        FROM membership_seat s3
        JOIN app_user u3 ON u3.user_id = s3.member_id
        WHERE s3.group_id = v.group_id
          AND u3.user_id = 42)
ORDER BY v.host_credit DESC, v.seats_left ASC
LIMIT 5;
