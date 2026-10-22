-- =====================================================================
-- LinkedIn, reverse-engineered | 03_queries.sql
-- 18 analytical queries over the hiring loop, grouped by difficulty.
--
-- Every statement is standalone: select it in Navicat and press Ctrl+R.
-- Requires 01_schema.sql + 02_seed.sql (04 is optional for these reads).
-- All statements are ONLY_FULL_GROUP_BY-safe and alias no reserved word.
--
-- Group A (Q01-Q06)  reporting: joins, aggregation, anti-joins
-- Group B (Q07-Q13)  business questions: funnels, referrals, skill gaps
-- Group C (Q14-Q18)  advanced: CTEs, window functions, recursion
-- =====================================================================
USE linkedin_db;
SET NAMES utf8mb4;

-- #####################################################################
-- GROUP A - FOUNDATION (6)
-- #####################################################################

-- @query Q01 | Open roles in Singapore: pay band, how long the seat has been empty, how contested it is
-- technique: 4-table join + scalar subquery + computed column + ORDER BY / LIMIT
SELECT j.job_id,
       j.title,
       c.company_name,
       c.industry,
       j.seniority,
       j.work_mode,
       ROUND((j.salary_min + j.salary_max) / 2)                     AS salary_mid_usd,
       DATEDIFF('2026-10-15', j.posted_at)                           AS days_open,
       (SELECT COUNT(*) FROM application a WHERE a.job_id = j.job_id) AS applicants
FROM job_posting j
JOIN company c ON c.company_id = j.company_id
WHERE j.status   = 'OPEN'
  AND j.country  = 'SG'
ORDER BY salary_mid_usd DESC, days_open DESC, j.job_id
LIMIT 12;

-- @query Q02 | Talent directory: the deepest open-to-work profiles, with credentials and reach
-- technique: LEFT JOIN + multi-aggregate + GROUP_CONCAT + correlated count + GROUP BY every non-aggregate
SELECT m.member_id,
       m.full_name,
       m.headline,
       m.city,
       COUNT(DISTINCT ms.skill_id)                                  AS skills,
       COUNT(DISTINCT e.education_id)                               AS degrees,
       GROUP_CONCAT(DISTINCT e.degree ORDER BY e.degree SEPARATOR '/') AS degree_levels,
       (SELECT COUNT(*) FROM connection cn
         WHERE cn.member_a_id = m.member_id OR cn.member_b_id = m.member_id) AS connections
FROM member m
LEFT JOIN member_skill ms ON ms.member_id = m.member_id
LEFT JOIN education    e  ON e.member_id  = m.member_id
WHERE m.open_to_work = 1
  AND m.years_experience >= 4
GROUP BY m.member_id, m.full_name, m.headline, m.city
ORDER BY skills DESC, connections DESC, m.member_id
LIMIT 10;

-- @query Q03 | The five most contested open postings, application by application
-- technique: derived table with LIMIT + 4-table join + status filter
SELECT t.job_id,
       t.title,
       t.company_name,
       t.applicants,
       m.full_name                                   AS candidate,
       a.status,
       DATE(a.applied_at)                             AS applied_on,
       DATEDIFF('2026-10-15', a.applied_at)           AS days_since_apply
FROM (SELECT j.job_id, j.title, c.company_name, COUNT(*) AS applicants
      FROM job_posting j
      JOIN company  c ON c.company_id = j.company_id
      JOIN application a ON a.job_id = j.job_id
      WHERE j.status = 'OPEN'
      GROUP BY j.job_id, j.title, c.company_name
      ORDER BY applicants DESC, j.job_id
      LIMIT 5) t
JOIN application a ON a.job_id = t.job_id
JOIN member      m ON m.member_id = a.member_id
ORDER BY t.applicants DESC, t.job_id, a.applied_at;

-- @query Q04 | What the market actually asks for: skills ranked by hard requirement, with share of all postings
-- technique: 3-table join + conditional SUM + share of a scalar total + HAVING
SELECT s.skill_name,
       s.skill_family,
       SUM(js.importance = 'REQUIRED')                                    AS required_postings,
       SUM(js.importance = 'PREFERRED')                                   AS preferred_postings,
       COUNT(*)                                                           AS postings_asking,
       ROUND(100 * COUNT(*) / (SELECT COUNT(*) FROM job_posting
                                WHERE status <> 'DRAFT'), 1)              AS pct_of_postings
FROM skill s
JOIN job_skill    js ON js.skill_id = s.skill_id
JOIN job_posting  j  ON j.job_id    = js.job_id AND j.status <> 'DRAFT'
GROUP BY s.skill_id, s.skill_name, s.skill_family
HAVING required_postings >= 5
ORDER BY required_postings DESC, preferred_postings DESC, s.skill_name
LIMIT 15;

-- @query Q05 | Company hiring scorecard: volume, conversion and speed
-- technique: LEFT JOIN + COUNT DISTINCT + SUM(CASE) + conditional AVG + HAVING
SELECT c.company_name,
       c.industry,
       COUNT(DISTINCT j.job_id)                                              AS postings,
       COUNT(a.application_id)                                               AS applications,
       SUM(a.status = 'HIRED')                                               AS hires,
       ROUND(100 * SUM(a.status = 'HIRED') / COUNT(a.application_id), 1)     AS hire_rate_pct,
       ROUND(AVG(CASE WHEN a.status = 'HIRED'
                      THEN TIMESTAMPDIFF(DAY, a.applied_at, a.decided_at) END), 1) AS avg_days_to_hire
FROM company c
JOIN job_posting j ON j.company_id = c.company_id
LEFT JOIN application a ON a.job_id = j.job_id
GROUP BY c.company_id, c.company_name, c.industry
HAVING applications >= 4
ORDER BY hire_rate_pct DESC, hires DESC, applications DESC
LIMIT 12;

-- @query Q06 | Dormant talent: open to work, experienced, but no application in the last 90 days
-- technique: anti-join (LEFT JOIN ... IS NULL) + multiple LEFT JOIN aggregates + HAVING on a count
SELECT m.member_id,
       m.full_name,
       m.city,
       m.years_experience,
       COUNT(DISTINCT ms.skill_id)      AS skills,
       COUNT(DISTINCT e.education_id)   AS degrees,
       COUNT(DISTINCT a.application_id) AS applications_since_july
FROM member m
LEFT JOIN member_skill ms ON ms.member_id = m.member_id
LEFT JOIN education    e  ON e.member_id  = m.member_id
LEFT JOIN application  a  ON a.member_id  = m.member_id
                         AND a.applied_at >= '2026-07-17'
WHERE m.open_to_work = 1
  AND m.years_experience >= 3
GROUP BY m.member_id, m.full_name, m.city, m.years_experience
HAVING applications_since_july = 0
ORDER BY skills DESC, m.years_experience DESC, m.member_id
LIMIT 15;

-- #####################################################################
-- GROUP B - BUSINESS QUESTIONS (7)
-- #####################################################################

-- @query Q07 | Which sourcing channel actually converts? Funnel by source channel
-- technique: CTE + EXISTS-as-boolean aggregation + NULLIF-safe rates
WITH channel AS (
  SELECT a.source_channel,
         COUNT(*)                                                        AS applications,
         SUM(EXISTS (SELECT 1 FROM interview i
                      WHERE i.application_id = a.application_id))        AS interviewed,
         SUM(a.status IN ('OFFER', 'HIRED'))                             AS offers,
         SUM(a.status = 'HIRED')                                         AS hires
  FROM application a
  GROUP BY a.source_channel
)
SELECT source_channel,
       applications,
       interviewed,
       offers,
       hires,
       ROUND(100 * interviewed / applications, 1)                        AS interview_rate_pct,
       ROUND(100 * offers      / NULLIF(interviewed, 0), 1)              AS offer_rate_from_interview_pct,
       ROUND(100 * hires       / applications, 1)                        AS end_to_end_hire_rate_pct
FROM channel
ORDER BY end_to_end_hire_rate_pct DESC, applications DESC;

-- @query Q08 | The referral programme: who refers well, and what it costs
-- technique: CTE-free 5-table join + conditional SUM for money + GROUP BY on a nullable join key
SELECT r.referrer_id,
       m.full_name                                    AS referrer,
       c.company_name                                 AS employer,
       COUNT(*)                                       AS referrals,
       SUM(a.status = 'HIRED')                        AS hires,
       ROUND(100 * SUM(a.status = 'HIRED') / COUNT(*), 1) AS hire_rate_pct,
       SUM(CASE WHEN r.bonus_status = 'PAID'
                THEN r.bonus_amount ELSE 0 END)       AS bonus_paid_usd,
       SUM(CASE WHEN r.bonus_status = 'PENDING'
                THEN r.bonus_amount ELSE 0 END)       AS bonus_pending_usd
FROM referral r
JOIN member      m ON m.member_id = r.referrer_id
JOIN application a ON a.application_id = r.application_id
LEFT JOIN experience e ON e.member_id = r.referrer_id AND e.is_current = 1
LEFT JOIN company    c ON c.company_id = e.company_id
GROUP BY r.referrer_id, m.full_name, c.company_name
ORDER BY hires DESC, referrals DESC, hire_rate_pct DESC
LIMIT 12;

-- @query Q09 | Skill-gap matching for one candidate (member 231): jobs they half-qualify for, and what they lack
-- technique: CTE + LEFT JOIN aggregate + correlated GROUP_CONCAT subquery + EXISTS flag
-- parameter: member 231 (Hana Choi, Risk Analyst at Allianz, Shanghai; 29 partially matching open roles) in the three member predicates
WITH required AS (
  SELECT js.job_id, js.skill_id, js.min_proficiency
  FROM job_skill js
  WHERE js.importance = 'REQUIRED'
),
per_job AS (
  SELECT r.job_id,
         COUNT(*)              AS required_total,
         COUNT(ms.skill_id)    AS matched_skills
  FROM required r
  LEFT JOIN member_skill ms ON ms.skill_id = r.skill_id AND ms.member_id = 231 AND ms.proficiency >= r.min_proficiency
  GROUP BY r.job_id
)
SELECT j.job_id,
       j.title,
       c.company_name,
       j.city,
       pj.required_total,
       pj.matched_skills,
       ROUND(100 * pj.matched_skills / pj.required_total, 1) AS match_pct,
       (SELECT GROUP_CONCAT(s.skill_name ORDER BY s.skill_name SEPARATOR ', ')
          FROM required r2
          JOIN skill s ON s.skill_id = r2.skill_id
         WHERE r2.job_id = j.job_id
           AND NOT EXISTS (SELECT 1 FROM member_skill ms2
                            WHERE ms2.member_id = 231
                              AND ms2.skill_id = r2.skill_id
                              AND ms2.proficiency >= r2.min_proficiency)) AS missing_required,
       EXISTS (SELECT 1 FROM application a
                WHERE a.job_id = j.job_id AND a.member_id = 231) AS already_applied
FROM per_job pj
JOIN job_posting j ON j.job_id = pj.job_id
JOIN company     c ON c.company_id = j.company_id
WHERE j.status = 'OPEN'
  AND pj.matched_skills * 2 >= pj.required_total
ORDER BY match_pct DESC, pj.required_total DESC, j.job_id
LIMIT 12;

-- @query Q10 | Where the hiring loop spends its time, by seniority
-- technique: CTE + pre-aggregated interview span + LEFT JOIN + four AVG date differences
WITH hires AS (
  SELECT a.application_id,
         a.applied_at,
         a.decided_at,
         j.seniority
  FROM application a
  JOIN job_posting j ON j.job_id = a.job_id
  WHERE a.status = 'HIRED'
),
span AS (
  SELECT i.application_id,
         MIN(i.scheduled_at) AS first_round,
         MAX(i.scheduled_at) AS last_round,
         COUNT(*)            AS rounds
  FROM interview i
  GROUP BY i.application_id
)
SELECT h.seniority,
       COUNT(*)                                                          AS hires,
       ROUND(AVG(TIMESTAMPDIFF(DAY, h.applied_at, s.first_round)), 1)     AS days_to_first_interview,
       ROUND(AVG(TIMESTAMPDIFF(DAY, s.first_round, s.last_round)), 1)     AS days_across_interviews,
       ROUND(AVG(TIMESTAMPDIFF(DAY, s.last_round, h.decided_at)), 1)      AS days_to_decision,
       ROUND(AVG(TIMESTAMPDIFF(DAY, h.applied_at, h.decided_at)), 1)      AS total_days,
       ROUND(AVG(s.rounds), 1)                                            AS avg_rounds
FROM hires h
LEFT JOIN span s ON s.application_id = h.application_id
GROUP BY h.seniority
ORDER BY FIELD(h.seniority, 'INTERN', 'JUNIOR', 'MID', 'SENIOR', 'LEAD', 'PRINCIPAL', 'DIRECTOR');

-- @query Q11 | Interviewer calibration: who runs a hard bar, who passes almost everyone?
-- technique: CTE + conditional SUM + NULLIF-safe pass rate + HAVING on interview volume
WITH per_interviewer AS (
  SELECT i.interviewer_id,
         COUNT(*)                                                    AS interviews,
         SUM(i.outcome IN ('PASS', 'FAIL'))                          AS decided,
         SUM(i.outcome = 'PASS')                                     AS passed,
         AVG(i.score)                                                AS avg_score,
         AVG(TIMESTAMPDIFF(DAY, a.applied_at, i.scheduled_at))       AS avg_days_from_apply
  FROM interview i
  JOIN application a ON a.application_id = i.application_id
  GROUP BY i.interviewer_id
)
SELECT m.full_name                                                    AS interviewer,
       c.company_name                                                 AS employer,
       l.interviews,
       l.decided,
       ROUND(100 * l.passed / NULLIF(l.decided, 0), 1)                 AS pass_rate_pct,
       ROUND(l.avg_score, 2)                                          AS avg_score,
       ROUND(l.avg_days_from_apply, 1)                                AS avg_days_from_apply
FROM per_interviewer l
JOIN member m ON m.member_id = l.interviewer_id
LEFT JOIN experience e ON e.member_id = l.interviewer_id AND e.is_current = 1
LEFT JOIN company    c ON c.company_id = e.company_id
WHERE l.interviews >= 3
  AND l.decided >= 2
ORDER BY pass_rate_pct ASC, l.interviews DESC, interviewer
LIMIT 12;

-- @query Q12 | Where the company's own demand outruns its internal supply
-- technique: two CTEs + LEFT JOIN on the gap + COALESCE + HAVING on demand
WITH demand AS (
  SELECT j.company_id, js.skill_id, COUNT(DISTINCT j.job_id) AS postings_asking
  FROM job_posting j
  JOIN job_skill   js ON js.job_id = j.job_id
  WHERE j.status IN ('OPEN', 'ON_HOLD')
    AND js.importance = 'REQUIRED'
  GROUP BY j.company_id, js.skill_id
),
supply AS (
  SELECT e.company_id, ms.skill_id, COUNT(DISTINCT ms.member_id) AS holders
  FROM experience   e
  JOIN member_skill ms ON ms.member_id = e.member_id AND ms.proficiency >= 3
  WHERE e.is_current = 1
  GROUP BY e.company_id, ms.skill_id
)
SELECT c.company_name,
       s.skill_name,
       s.skill_family,
       d.postings_asking,
       COALESCE(sup.holders, 0)                                  AS internal_holders,
       d.postings_asking - COALESCE(sup.holders, 0)              AS unmet_demand
FROM demand d
JOIN company c ON c.company_id = d.company_id
JOIN skill   s ON s.skill_id   = d.skill_id
LEFT JOIN supply sup ON sup.company_id = d.company_id AND sup.skill_id = d.skill_id
WHERE d.postings_asking >= 2
ORDER BY unmet_demand DESC, d.postings_asking DESC, c.company_name
LIMIT 15;

-- @query Q13 | Postings whose screening stage has gone quiet
-- technique: anti-join predicate + correlated count + join to the recruiter member
SELECT a.application_id,
       c.company_name,
       j.title,
       m.full_name                                AS candidate,
       rec.full_name                              AS recruiter,
       DATEDIFF('2026-10-15', a.applied_at)        AS days_in_screening,
       (SELECT COUNT(*) FROM application a2 WHERE a2.job_id = j.job_id) AS competing_applicants
FROM application a
JOIN job_posting j   ON j.job_id     = a.job_id
JOIN company     c   ON c.company_id = j.company_id
JOIN member      m   ON m.member_id  = a.member_id
JOIN member      rec ON rec.member_id = j.recruiter_id
WHERE a.status = 'SCREENING'
  AND a.applied_at < '2026-09-24'
ORDER BY days_in_screening DESC, competing_applicants DESC
LIMIT 12;

-- #####################################################################
-- GROUP C - ADVANCED (5)
-- #####################################################################

-- @query Q14 | Hiring momentum: monthly volume, 3-month moving average, running hires, month-on-month change
-- technique: two CTEs + window SUM/AVG with ROWS frames + LAG
WITH monthly AS (
  SELECT DATE_FORMAT(a.applied_at, '%Y-%m') AS ym,
         COUNT(*)                            AS applications,
         SUM(a.status = 'HIRED')             AS hires
  FROM application a
  GROUP BY DATE_FORMAT(a.applied_at, '%Y-%m')
),
interviews AS (
  SELECT DATE_FORMAT(i.scheduled_at, '%Y-%m') AS ym,
         COUNT(*)                              AS interviews
  FROM interview i
  GROUP BY DATE_FORMAT(i.scheduled_at, '%Y-%m')
)
SELECT m.ym,
       m.applications,
       COALESCE(iv.interviews, 0)                                            AS interviews,
       m.hires,
       ROUND(AVG(m.applications) OVER (ORDER BY m.ym
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1)                   AS app_3m_moving_avg,
       SUM(m.hires) OVER (ORDER BY m.ym ROWS UNBOUNDED PRECEDING)            AS cumulative_hires,
       m.applications - LAG(m.applications) OVER (ORDER BY m.ym)             AS app_mom_change
FROM monthly m
LEFT JOIN interviews iv ON iv.ym = m.ym
ORDER BY m.ym;

-- @query Q15 | Which company converts best inside its own industry?
-- technique: CTE + RANK/DENSE_RANK with PARTITION BY + SUM() OVER for share + HAVING
WITH stats AS (
  SELECT c.company_id,
         c.company_name,
         c.industry,
         COUNT(DISTINCT j.job_id)      AS postings,
         COUNT(a.application_id)       AS applications,
         SUM(a.status = 'HIRED')       AS hires
  FROM company c
  LEFT JOIN job_posting j ON j.company_id = c.company_id
  LEFT JOIN application a ON a.job_id = j.job_id
  GROUP BY c.company_id, c.company_name, c.industry
  HAVING applications >= 2
)
SELECT company_name,
       industry,
       postings,
       applications,
       hires,
       ROUND(100 * hires / applications, 1)                                       AS hire_rate_pct,
       RANK() OVER (PARTITION BY industry ORDER BY hires / applications DESC, hires DESC) AS rank_in_industry,
       DENSE_RANK() OVER (ORDER BY hires DESC, applications DESC)                  AS rank_by_volume,
       ROUND(100 * hires / NULLIF(SUM(hires) OVER (PARTITION BY industry), 0), 1) AS pct_of_industry_hires
FROM stats
ORDER BY industry, rank_in_industry, company_name
LIMIT 24;

-- @query Q16 | Recruiter leaderboard: volume, conversion, rank and distance to the leader
-- technique: CTE + RANK + PERCENT_RANK + LAG over the ranked order
WITH per_recruiter AS (
  SELECT j.recruiter_id,
         COUNT(DISTINCT j.job_id)         AS postings,
         COUNT(a.application_id)          AS applications,
         SUM(a.status = 'HIRED')          AS hires
  FROM job_posting j
  LEFT JOIN application a ON a.job_id = j.job_id
  GROUP BY j.recruiter_id
  HAVING applications >= 3
)
SELECT m.full_name                                                        AS recruiter,
       c.company_name                                                     AS employer,
       p.postings,
       p.applications,
       p.hires,
       ROUND(100 * p.hires / p.applications, 1)                           AS hire_rate_pct,
       RANK() OVER (ORDER BY p.hires DESC, p.applications DESC)            AS overall_rank,
       ROUND(PERCENT_RANK() OVER (ORDER BY p.hires / p.applications), 2)   AS conversion_percentile,
       LAG(p.hires) OVER (ORDER BY p.hires DESC, p.applications DESC)      AS hires_of_rank_above
FROM per_recruiter p
JOIN member m ON m.member_id = p.recruiter_id
LEFT JOIN experience e ON e.member_id = p.recruiter_id AND e.is_current = 1
LEFT JOIN company    c ON c.company_id = e.company_id
ORDER BY overall_rank, recruiter
LIMIT 12;

-- @query Q17 | Skill scarcity index: demand against proven supply, quartile-ranked
-- technique: two CTEs + window NTILE over a ratio + CASE bucketing + NULLIF division
WITH demand AS (
  SELECT js.skill_id, COUNT(*) AS postings
  FROM job_skill js
  JOIN job_posting j ON j.job_id = js.job_id AND j.status <> 'DRAFT'
  GROUP BY js.skill_id
),
supply AS (
  SELECT ms.skill_id, COUNT(*) AS strong_holders
  FROM member_skill ms
  WHERE ms.proficiency >= 4
  GROUP BY ms.skill_id
)
SELECT s.skill_name,
       s.skill_family,
       s.is_emerging,
       d.postings,
       COALESCE(sup.strong_holders, 0)                                  AS strong_holders,
       ROUND(d.postings / COALESCE(sup.strong_holders, 0), 2)           AS postings_per_holder,
       NTILE(4) OVER (ORDER BY d.postings / COALESCE(sup.strong_holders, 0) DESC) AS scarcity_quartile,
       CASE
         WHEN d.postings / COALESCE(sup.strong_holders, 0) >= 1.0 THEN 'ACUTE'
         WHEN d.postings / COALESCE(sup.strong_holders, 0) >= 0.5 THEN 'TIGHT'
         WHEN d.postings / COALESCE(sup.strong_holders, 0) >= 0.2 THEN 'BALANCED'
         ELSE 'ABUNDANT'
       END                                                              AS market_state
FROM demand d
JOIN skill s ON s.skill_id = d.skill_id
LEFT JOIN supply sup ON sup.skill_id = d.skill_id
WHERE d.postings >= 3
ORDER BY postings_per_holder DESC, d.postings DESC;

-- @query Q18 | Warm-intro sourcing: candidates within two connection hops of the hiring team
-- technique: recursive CTE over the undirected connection graph + MIN(hops) reduction + skill match + anti-join
-- parameter: job 79 (Delivery Manager at IBM, Austin; 35 reachable candidates) in the target CTE and in the required_total subquery
WITH RECURSIVE target AS (
  SELECT j.job_id, j.company_id
  FROM job_posting j
  WHERE j.job_id = 79
),
reach (member_id, hops, bridge_id) AS (
  SELECT e.member_id, 0, e.member_id
  FROM experience e
  JOIN target t ON t.company_id = e.company_id
  WHERE e.is_current = 1
  UNION ALL
  SELECT IF(c.member_a_id = r.member_id, c.member_b_id, c.member_a_id),
         r.hops + 1,
         r.bridge_id
  FROM reach r
  JOIN connection c
    ON c.member_a_id = r.member_id OR c.member_b_id = r.member_id
  WHERE r.hops < 2
),
closest AS (
  SELECT member_id, MIN(hops) AS hops, MIN(bridge_id) AS bridge_id
  FROM reach
  WHERE hops > 0
  GROUP BY member_id
),
matched AS (
  SELECT ms.member_id, COUNT(*) AS required_held
  FROM member_skill ms
  JOIN job_skill    js ON js.skill_id = ms.skill_id
  JOIN target       t  ON t.job_id    = js.job_id
  WHERE js.importance = 'REQUIRED'
    AND ms.proficiency >= js.min_proficiency
  GROUP BY ms.member_id
)
SELECT m.member_id,
       m.full_name,
       m.city,
       m.years_experience,
       cl.hops                                                            AS degrees_away,
       b.full_name                                                        AS bridge_to_hiring_team,
       mt.required_held,
       (SELECT COUNT(*) FROM job_skill js2
         WHERE js2.job_id = 79 AND js2.importance = 'REQUIRED')            AS required_total
FROM closest cl
JOIN member m ON m.member_id = cl.member_id
JOIN member b ON b.member_id = cl.bridge_id
JOIN matched mt ON mt.member_id = cl.member_id
WHERE m.open_to_work = 1
  AND mt.required_held >= 2
  AND NOT EXISTS (SELECT 1 FROM application a
                   WHERE a.job_id = 79 AND a.member_id = m.member_id)
  AND NOT EXISTS (SELECT 1 FROM experience e2
                   WHERE e2.member_id = m.member_id AND e2.is_current = 1
                     AND e2.company_id = (SELECT company_id FROM target))
ORDER BY cl.hops, mt.required_held DESC, m.years_experience DESC, m.member_id
LIMIT 15;

-- =====================================================================
-- End of file: 18 statements, 6 + 7 + 5.
-- =====================================================================
