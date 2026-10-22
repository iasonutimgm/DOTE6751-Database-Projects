# SubSplit — Escrow-Protected Subscription Sharing

DOTE 6751 Database Systems · Group Project · November 2026

**Start here → `File_Guide_文件阅读指南\File_Guide_CN.docx`.** It explains every file in this folder, in what order to
run them, and how to verify that the database is correct.

## The three commands you probably want

```sql
-- 1. rebuild the whole database (MySQL 8.0, from the sql/ folder)
SOURCE 01_schema.sql;
SOURCE 02_seed.sql;
SOURCE 04_views_triggers.sql;

-- 2. check that it is healthy: every row should read PASS
SOURCE 06_checks.sql;

-- 3. look at the analysis
SOURCE 03_queries.sql;
```

In Navicat: right-click the connection → **Run SQL File** → `sql/subsplit_db_full.sql`.
That restores the database, its data, its views and its triggers in one step.

## What is where

| Folder | What it holds |
|---|---|
| `design/` | the argument: requirements, E-R catalogue, relational schema, 3NF proof, constraints, rationale |
| `sql/` | the implementation: DDL, seed, 18 queries, views and triggers, transactions, checks, full dump |
| `erd/` | the pictures: conceptual E-R, logical schema, three module views, editable sources |
| `slides/` | what gets presented: the deck, its PDF, the script, the Q&A sheet, the narrative |
| `query_results/` | the output of every query, as CSV, plus the table images used in the deck |

## One-line summary

Eleven relations, fifteen foreign keys, seventy-six attributes, BCNF, five triggers, two
views, eighteen queries — all of it running on MySQL 8.0.40 and verified by a twelve-point
acceptance script.
