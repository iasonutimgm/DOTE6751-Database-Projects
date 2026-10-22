-- =====================================================================
-- LinkedIn (reverse-engineered) | 00_run_all.sql
-- One-shot rebuild, in dependency order.
--
-- From the command line (run inside this folder):
--     mysql -u root -p < 00_run_all.sql
--
-- Order matters: 02_seed.sql must run while the triggers do not yet
-- exist, because the seed contains historical rows (applications
-- withdrawn after interviews) that the live guards would rightly refuse.
-- =====================================================================

SOURCE 01_schema.sql;
SOURCE 02_seed.sql;
SOURCE 04_views_triggers.sql;
SOURCE 03_queries.sql;
SOURCE 05_transactions.sql;
SOURCE 06_checks.sql;
