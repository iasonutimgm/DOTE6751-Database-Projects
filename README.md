# DOTE6751 Database Systems —  Project

Two end-to-end database design and implementation projects for **DOTE 6751 Database Systems**. Both are built for **MySQL 8.0** and include the full design documentation, ER diagrams, SQL implementation, query results, and presentation materials.

## Projects

### 1. LinkedIn — Hiring Loop, Referral Chain, Skill Gap

A reverse-engineered LinkedIn-style hiring platform covering identity, demand, and the hiring loop.

- **Scale:** 12 relations, 17 foreign keys, 4 views, 4 triggers, 18 analysis queries, 22 cross-table invariants
- **Start here:** [`DOTE6751_LinkedIn/README.md`](DOTE6751_LinkedIn/README.md)
- **SQL:** [`DOTE6751_LinkedIn/sql/`](DOTE6751_LinkedIn/sql/)
- **Slides:** [`DOTE6751_LinkedIn/slides/`](DOTE6751_LinkedIn/slides/)

### 2. SubSplit — Escrow-Protected Subscription Sharing

A subscription-sharing platform where payments are held in escrow until a group subscription is confirmed.

- **Scale:** 11 relations, 15 foreign keys, 76 attributes, BCNF, 5 triggers, 2 views, 18 analysis queries
- **Start here:** [`DOTE6751_SubSplit/README.md`](DOTE6751_SubSplit/README.md)
- **SQL:** [`DOTE6751_SubSplit/sql/`](DOTE6751_SubSplit/sql/)
- **Slides:** [`DOTE6751_SubSplit/PresentationSlides/`](DOTE6751_SubSplit/PresentationSlides/)

## Repository layout

```
DOTE6751-Database-Projects/
├── DOTE6751_LinkedIn/
│   ├── design/          requirements, ER catalogue, relational schema, 3NF proof
│   ├── sql/             DDL, seed, queries, views/triggers, transactions, checks, full dump
│   ├── erd/             conceptual and logical ER diagrams (PNG + SVG)
│   ├── slides/          decks, narrative, speaking script, Q&A preparation
│   ├── query_results/   CSV output and consistency report
│   └── build/           generator scripts
└── DOTE6751_SubSplit/
    ├── design/          requirements, ER catalogue, relational schema, BCNF proof
    ├── sql/             DDL, seed, queries, views/triggers, transactions, checks, full dump
    ├── erd/             conceptual, logical, and module ER diagrams
    ├── PresentationSlides/  decks (EN/CN), script, Q&A, narrative
    └── query_results/   CSV output and summary
```

## Quick start

Each project ships with a one-file restore script:

```sql
-- LinkedIn
SOURCE DOTE6751_LinkedIn/sql/linkedin_db_full.sql;

-- SubSplit
SOURCE DOTE6751_SubSplit/sql/subsplit_db_full.sql;
```

Or run the numbered scripts in order: `01_schema.sql` → `02_seed.sql` → `04_views_triggers.sql` → `03_queries.sql`.

## Notes

- All data is synthetic; no real LinkedIn or SubSplit user data is included.
- Generated Office/PDF deliverables are committed alongside their Markdown sources so the reports can be read without rebuilding.
