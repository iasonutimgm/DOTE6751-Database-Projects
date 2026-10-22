-- =====================================================================
-- SubSplit | 00_run_all.sql
-- One-shot rebuild, in dependency order.
--
-- From the command line (run inside this folder):
--     mysql -u root -p < 00_run_all.sql
--
-- From Navicat: open this file and execute it. If your client does not
-- support SOURCE, run the four files in the order shown below instead —
-- 01, then 02, then 04, then 03.
--
-- Order matters: 02_seed.sql must run while the triggers do not yet
-- exist, because the seed contains historical states (frozen groups,
-- closed groups) that the live capacity trigger would rightly refuse.
-- =====================================================================

SOURCE 01_schema.sql;
SOURCE 02_seed.sql;
SOURCE 04_views_triggers.sql;
SOURCE 03_queries.sql;
SOURCE 05_transactions.sql;
SOURCE 06_checks.sql;
