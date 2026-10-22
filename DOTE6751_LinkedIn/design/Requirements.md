# LinkedIn, Reverse-Engineered — Requirements and Scope

**Course:** DOTE 6751 Database Systems · Group Project · November 2026
**Team:** Xuanmo AN, Yi HOU, Zhao Han HUANG, Jinyu LI, Yitong NI, Shujing YE, Shiyao ZHANG

## 1. The problem

LinkedIn does not publish its schema. It publishes behaviour: a member can follow a
company, save a job, be referred by a colleague, sit through three interview rounds and
receive an offer, and at every step the product shows exactly the records that step
creates. This project reconstructs the logical database behind one closed loop of that
product — **a company advertises a job, a member applies, is interviewed, and is
hired** — and extends it with the two mechanisms that make the loop interesting in
practice: the **referral chain** and **skill-gap matching**.

The reconstruction is not a copy of LinkedIn's physical design, which is a distributed
graph store with denormalised feeds. It is the smallest relational schema that can
answer the questions the product visibly answers, derived with the mapping rules of
Silberschatz, Korth and Sudarshan, *Database System Concepts*, 7th ed., Chapter 6
(§6.7, reducing E-R diagrams to relational schemas), and validated against the normal
forms of Chapter 7.

## 2. Actors

| Actor | Description | Main goals |
|---|---|---|
| **Member** | A natural person with a profile, skills, education and work history | Be discovered, apply, be referred, get hired |
| **Recruiter** | A member acting for an employer; posts and owns postings | Fill a seat quickly and cheaply |
| **Referrer** | A member who works at the hiring company and recommends a candidate | Help a contact, earn the bonus |
| **Interviewer** | A member of the hiring team who runs a round | Assess candidates consistently |
| **Analyst** | Reads the warehouse-style queries (Q01–Q18) | Understand funnel, scarcity and cost |

The model deliberately keeps *one* member entity: recruiter, referrer, interviewer and
candidate are the same person seen through different relationship sets. Only the
`member_skill`, `experience` and `education` tables distinguish what a person knows from
what a posting asks for.

## 3. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | A member registers with a unique e-mail, a location, years of experience and a visibility setting. |
| FR-2 | A member records zero or more education entries and one or more experience entries; at most one experience is the current position. |
| FR-3 | A member claims skills from a controlled vocabulary with a proficiency level (1–5), years of use and an endorsement count. |
| FR-4 | A company is described once: industry, head-quarters country, head-count band, founding year, verification flag. |
| FR-5 | A recruiter posts a job with title, seniority, employment type, work mode, location, salary band, minimum experience and a number of openings. |
| FR-6 | A posting declares the skills it requires or prefers, each with a minimum proficiency; at least three are hard requirements. |
| FR-7 | A member applies once per posting, through one of three channels: direct, referral, sourcing. |
| FR-8 | An application moves through SUBMITTED → SCREENING → INTERVIEW → OFFER → HIRED, or leaves the loop through REJECTED or WITHDRAWN; no other transition is legal. |
| FR-9 | A posting can only be interviewed for once the application has reached the interview stage; rounds are numbered 1..n without gaps. |
| FR-10 | An interview records its round, format, schedule, duration, interviewer, outcome and a 1–5 score. |
| FR-11 | A referral exists only for an application that arrived through the referral channel; the referrer must currently work at the hiring company and cannot be the candidate. |
| FR-12 | A referral carries a relationship type, a referral date, a bonus amount and a bonus state. |
| FR-13 | A posting is closed only after its last decision; a member may not apply to a draft posting or to their own current employer. |
| FR-14 | Hires per posting may never exceed its number of openings. |
| FR-15 | A member is connected to another member at most once, and the edge is stored in canonical order. |
| FR-16 | Analysts can answer, from the database alone: channel conversion, referral return on bonus, individual skill gaps, cycle time, interviewer calibration, skill scarcity, and warm-introduction paths. |

## 4. Non-functional requirements

- **Integrity over convenience.** Every rule in section 3 that can be expressed
  declaratively is a `PRIMARY KEY`, `UNIQUE`, `FOREIGN KEY` or `CHECK`; the four rules
  that reach across tables are triggers (`sql/04_views_triggers.sql`).
- **Reproducibility.** A single seeded script rebuilds the database; the generator is
  deterministic (`random.Random(20261115)`), so every number in the report can be
  re-derived.
- **Portability.** Plain MySQL 8.0, no extensions, no stored procedures; the scripts run
  unchanged in Navicat and in the command-line client.
- **Read performance.** The two hottest reads — "open roles in a city" and "this
  member's applications" — are covered by composite indexes; no query in `03_queries.sql`
  scans a table it could seek.
- **Honesty about limits.** Where the product clearly has behaviour we cannot see (stage
  timestamps, recruiter notes, offer negotiation), the schema does not invent it; the
  limitation is recorded in `Design_Rationale.md` §7.

## 5. Scope

**In scope.** The logical schema (12 tables), its constraints, a self-consistent seeded
instance (300 members, 60 companies, 120 postings, 250 applications), 18 analytical
queries, the E-R and relational design documents, and the presentation artefacts.

**Out of scope.** Physical storage and sharding, the feed and messaging subsystems,
search indexing, authentication, media storage, billing, and any personal data beyond
what a public profile shows. Salary is modelled as an annual USD band; the currency
column exists but the seed uses one currency (see A6).

## 6. Assumptions

| ID | Assumption |
|---|---|
| A1 | One application = one member × one posting; re-application after withdrawal is out of scope and blocked by `uk_app_job_member`. |
| A2 | Exactly one experience row per member may have `is_current = 1`; the current employer is therefore derived, never stored on `member`. |
| A3 | A referral is 1:1 with the application it produced; the candidate and the posting are read through that application, not repeated. |
| A4 | Interview outcomes are PASS, FAIL, NO_SHOW or PENDING; a PASS or FAIL must carry a score, a PENDING round must not. |
| A5 | Hires never exceed openings; a posting that fills its openings is closed. |
| A6 | All salaries are annual and expressed in USD; the seed therefore sets `currency = 'USD'` everywhere. |
| A7 | "Now" is fixed at the snapshot 2026-10-15 18:00; no timestamp in the seed is later, so results do not drift with the clock. |
| A8 | A member cannot apply to a posting of their current employer (the product blocks it silently; we make it a modelling rule). |
| A9 | Skills are a controlled vocabulary of 60 entries in eight families; free-text skills are out of scope. |
| A10 | Presentation date is November 2026; all narrative and speaker notes use that date. |

## 7. Success criteria

1. `01_schema.sql` loads on an empty MySQL 8.0 instance with `ONLY_FULL_GROUP_BY` enabled,
   creating 12 tables, 17 foreign keys and 25 check constraints.
2. `02_seed.sql` loads without a single constraint violation and passes the 22 cross-table
   consistency checks in `query_results/_consistency_report.json`.
3. All 18 queries in `03_queries.sql` execute standalone and write one CSV each.
4. Every table is in 3NF with the argument recorded per table in
   `Normalization_Proof.xlsx`.
5. The deck renders without overflow and every claim on a slide traces to a query result
   in `query_results/`.
