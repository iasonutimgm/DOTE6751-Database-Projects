# LinkedIn, Reverse-Engineered — Hiring Loop, Referral Chain, Skill Gap

DOTE 6751 Database Systems · Group Project · November 2026

**Start here → `File_Guide.docx`** (English) or **`File_Guide_CN.docx`** (中文). Either one lists
every file, the order to run them in, and how to prove the database is correct.

## The three commands you probably want

```sql
-- 1. rebuild (MySQL 8.0, from the sql/ folder)
SOURCE 01_schema.sql;
SOURCE 02_seed.sql;
SOURCE 04_views_triggers.sql;

-- 2. the analysis
SOURCE 03_queries.sql;
```

In Navicat: right-click the connection → **Run SQL File** → `sql/…` in the order above.

## What is where

| Folder | What it holds |
|---|---|
| `design/` | requirements, E-R catalogue, relational schema, 3NF proof, constraint inventory, design rationale, **product specification (CN/EN, Word + Markdown)** |
| `sql/` | DDL, seed, 18 queries, views and triggers, transaction episodes, acceptance checks, full dump |
| `erd/` | logical schema, Chen-style conceptual model, three module views, PNG + SVG |
| `slides/` | the English deck, **the Chinese deck**, the narrative, the speaking script, Q&A preparation, task allocation |
| `query_results/` | every query's output as CSV, plus the consistency report |
| `build/` | the generator scripts, so the whole package can be rebuilt from source |

## One-line summary

Twelve relations, seventeen foreign keys, four views, four triggers, eighteen queries, and
twenty-two cross-table invariants that all hold on a 300-member synthetic instance.
