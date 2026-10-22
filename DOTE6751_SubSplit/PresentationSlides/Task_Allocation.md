# SubSplit — Task Allocation

Required by the project guidelines: member, student ID, task, difficulty (1–5) and estimated
hours. The same table appears as the appendix slide of the deck.

All seven tasks are technical. The workload follows the build pipeline — model → schema →
data → queries → audit — so that every row maps to a concrete artefact in this package.

| Student | Student ID | Task | Difficulty (1–5) | Estimated hours |
|---|---|---|---|---|
| Xuanmo AN | 1155260677 | Conceptual E-R model: entities, relationships, cardinality limits, weak-entity decision | 4 | 11 |
| Yi HOU | 1155261383 | E-R to relations: §6.7 mapping rules, key placement, 3NF/BCNF proof | 5 | 13 |
| Zhao Han HUANG | 1155272384 | DDL and integrity constraints: CHECK, unique keys, referential actions, indexes | 5 | 12 |
| Jinyu LI | 1155261567 | Triggers and views: seat ceiling, default instrument, credential journal, balance upkeep | 5 | 12 |
| Yitong NI | 1155265810 | Deterministic seed generator and the transaction episodes | 4 | 10 |
| Shujing YE | 1155261750 | Eighteen queries: grouping, window functions, CTEs, result capture | 4 | 11 |
| Shiyao ZHANG | 1155261823 | Acceptance suite, fault injection and ledger reconciliation | 4 | 10 |

**Total: 79 hours.**

## How difficulty was scored

Difficulty reflects the number of concepts a task touches, not the number of lines written:

- **5** — the task can silently corrupt the design if done wrong (mapping to relations, the
  normal-form argument, trigger logic).
- **4** — the task requires several concepts to line up (seeded data that satisfies every
  constraint, queries that mix aggregation and window functions).
- **3** — substantial but sequential; no task in this package fell below 4 once the
  presentation work was taken out of the table.

## What "estimated hours" means

Agreed before the work started and used to split the effort fairly. The hours include reading,
drafting, running and revising, not just typing. Every member also reviewed one artefact they
did not author; that review time is inside their own number.

## Cross-review

| Artefact | Author | Reviewed by |
|---|---|---|
| Conceptual model and catalogue | Xuanmo AN | Shujing YE |
| Relational schema and 3NF proof | Yi HOU | Xuanmo AN |
| DDL and constraints | Zhao Han HUANG | Jinyu LI |
| Triggers and views | Jinyu LI | Yi HOU |
| Seed and transactions | Yitong NI | Shiyao ZHANG |
| Queries and result capture | Shujing YE | Zhao Han HUANG |
| Acceptance, fault injection, reconciliation | Shiyao ZHANG | Yitong NI |

## Shared decisions

Two design decisions were argued through by the whole group rather than owned by one person:

1. modelling the dispute as a manual review instead of an automatic refund;
2. removing the `email` column once the instance turned out to carry an implausible
   institutional address.
