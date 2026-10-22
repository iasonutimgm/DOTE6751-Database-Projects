# Relational Schema

**LinkedIn, reverse-engineered · DOTE 6751 · November 2026**

Notation: `R(**PK**, attr, …)` lists the relation schema, the primary key in **bold**
and foreign keys in *italic*. Each schema is followed by its foreign-key clauses and the
functional dependencies that hold on it (the full 3NF argument is in
`Normalization_Proof.xlsx`). The corresponding DDL is `sql/01_schema.sql`; the object
names below are the ones that script creates.

---

## 1. The twelve relation schemas

### 1.1 company
`company(**company_id**, company_name, industry, hq_country, size_band, founded_year, is_verified)`

- No foreign keys.
- FDs: `company_id → all`; `company_name → all` (candidate key).
- 7 attributes, 2 candidate keys.

### 1.2 member
`member(**member_id**, full_name, headline, email, country, city, years_experience, open_to_work, profile_visibility, joined_at)`

- No foreign keys. The current employer is **not** an attribute of this relation; it is
  derived from `experience` where `is_current = 1` (see §3.1 of `Design_Rationale.md`).
- FDs: `member_id → all`; `email → all` (candidate key).
- Note that `headline` is a snapshot string such as "Project Manager at Siemens" — it is
  a fact about the profile at write time, not a copy of `company_name`.

### 1.3 job_posting
`job_posting(**job_id**, *company_id*, *recruiter_id*, title, seniority, employment_type, work_mode, city, country, salary_min, salary_max, currency, min_years_experience, openings, status, posted_at, closed_at)`

- `company_id` → `company.company_id` (ON DELETE CASCADE)
- `recruiter_id` → `member.member_id` (ON DELETE RESTRICT — a recruiter who has posted
  cannot be deleted while the posting exists)
- FDs: `job_id → all`. No other determinant: `title` does not determine salary, because
  two postings with the same title at different companies carry different bands.

### 1.4 skill
`skill(**skill_id**, skill_name, skill_family, is_emerging)`

- FDs: `skill_id → all`; `skill_name → all` (candidate key).

### 1.5 member_skill
`member_skill(**member_id**, **skill_id**, proficiency, years_used, endorsement_count, added_at)`

- `member_id` → `member.member_id` (CASCADE)
- `skill_id` → `skill.skill_id` (CASCADE)
- FDs: `(member_id, skill_id) → proficiency, years_used, endorsement_count, added_at`.
  No FD from either attribute alone: two members with the same skill have different
  proficiency, and one member's two skills have different years of use.

### 1.6 job_skill
`job_skill(**job_id**, **skill_id**, importance, min_proficiency)`

- `job_id` → `job_posting.job_id` (CASCADE)
- `skill_id` → `skill.skill_id` (CASCADE)
- FDs: `(job_id, skill_id) → importance, min_proficiency`.

### 1.7 application
`application(**application_id**, *job_id*, *member_id*, source_channel, status, applied_at, decided_at, resume_version)`

- `job_id` → `job_posting.job_id` (CASCADE)
- `member_id` → `member.member_id` (CASCADE)
- `UNIQUE (job_id, member_id)` — the natural key, so the relation has two candidate keys.
- FDs: `application_id → all`; `(job_id, member_id) → all`.
- The pair `(job_id, member_id)` determining `source_channel` is the reason a member
  cannot apply twice through different channels; the unique constraint is the enforcement.

### 1.8 interview
`interview(**interview_id**, *application_id*, round_no, interview_type, scheduled_at, duration_min, *interviewer_id*, outcome, score)`

- `application_id` → `application.application_id` (CASCADE)
- `interviewer_id` → `member.member_id` (RESTRICT)
- `UNIQUE (application_id, round_no)`
- FDs: `interview_id → all`; `(application_id, round_no) → all`.
- `score` is nullable *by design*: a scheduled round has no score yet, and the CHECK
  `ck_int_score_outcome` ties nullability to the outcome instead of to the column.

### 1.9 referral
`referral(**referral_id**, *application_id* UNIQUE, *referrer_id*, relationship, referred_at, bonus_amount, bonus_status)`

- `application_id` → `application.application_id` (CASCADE), UNIQUE → 1:1
- `referrer_id` → `member.member_id` (RESTRICT)
- FDs: `referral_id → all`; `application_id → all`.
- `job_id` and `member_id` are **not** repeated here; see §4.4 of `Design_Rationale.md`.

### 1.10 education
`education(**education_id**, *member_id*, school_name, degree, field_of_study, start_year, end_year)`

- `member_id` → `member.member_id` (CASCADE)
- FDs: `education_id → all`. `(member_id, school_name, degree)` is a natural key that is
  not enforced; a duplicate degree entry is possible and is a known limitation.

### 1.11 experience
`experience(**experience_id**, *member_id*, *company_id*, title, start_date, end_date, is_current, current_member_id)`

- `member_id` → `member.member_id` (CASCADE, ON UPDATE RESTRICT because `member_id` is the
  base of a generated column — MySQL 8.0 restriction)
- `company_id` → `company.company_id` (CASCADE)
- `UNIQUE (current_member_id)` where `current_member_id` is
  `GENERATED ALWAYS AS (IF(is_current = 1, member_id, NULL)) VIRTUAL`
- FDs: `experience_id → all`.

### 1.12 connection
`connection(**member_a_id**, **member_b_id**, connected_at, connection_type)`

- `member_a_id` → `member.member_id` (CASCADE)
- `member_b_id` → `member.member_id` (CASCADE)
- `CHECK (member_a_id < member_b_id)` — part of the key semantics
- FDs: `(member_a_id, member_b_id) → connected_at, connection_type`.

---

## 2. Reduction from the E-R model (Silberschatz §6.7)

The seven reduction rules of §6.7 and where each one fires in this design:

| §6.7 rule | Textbook statement (paraphrased) | Application here |
|---|---|---|
| **6.7.1 Strong entity sets** | Each strong entity set becomes a relation with the same attributes; the entity identifier becomes the primary key. | `member`, `company`, `job_posting`, `skill`, `interview`, `connection` are taken over directly. |
| **6.7.2 Weak entity sets** | A weak entity set becomes a relation containing the owner's key plus its discriminator. | No weak entity is used. `application` is *not* weak: it has its own surrogate identifier and an independent lifetime after the posting closes. |
| **6.7.3 Relationship sets — 1:1** | Either participating relation receives the other's key as a foreign key; choose the one with total participation. | `referral` ← `application_id`. The referral side is total, the application side is partial, so the key goes to `referral` and is made UNIQUE. |
| **6.7.4 Relationship sets — 1:N** | The key of the "one" side migrates into the "many" side. | `job_posting.company_id`, `job_posting.recruiter_id`, `application.job_id`, `application.member_id`, `interview.application_id`, `interview.interviewer_id`, `referral.referrer_id`, `education.member_id`, `experience.member_id`, `experience.company_id`, `member_skill.member_id`, `job_skill.job_id`. |
| **6.7.5 Relationship sets — M:N** | A new relation is created whose key is the union of both keys. | `connection` (member ↔ member, self), `member_skill` and `job_skill` (each M:N with descriptive attributes). |
| **6.7.6 Multivalued attributes** | Each multivalued attribute becomes its own relation keyed by the owner plus the value. | "Skills of a member" and "skills a posting asks for" are modelled as `member_skill` / `job_skill` rather than as repeating groups. |
| **6.7.7 Generalisation / specialisation** | Each specialisation becomes a relation containing the superclass key plus its own attributes. | Not used: recruiter, referrer and interviewer are *roles* (different relationship sets over one entity), not subtypes. This avoids the join-per-role that a `recruiter` subtype would force on every query. |

### 2.1 Cardinality and participation, as implemented

| Relationship | Cardinality | Participation | Implementation | Enforcement |
|---|---|---|---|---|
| advertises | 1:N | posting total | `job_posting.company_id` NOT NULL | FK |
| employs | 1:N | experience total | `experience.company_id` NOT NULL | FK |
| studied | 1:N | education total | `education.member_id` NOT NULL | FK |
| worked | 1:N | experience total | `experience.member_id` NOT NULL | FK |
| claims | 1:N | member total | `member_skill.member_id` NOT NULL | FK + CHECK proficiency |
| held_as | 1:N | total | `member_skill.skill_id` NOT NULL | FK |
| requires | 1:N | posting total | `job_skill.job_id` NOT NULL | FK + trigger-free CHECK |
| asked_as | 1:N | total | `job_skill.skill_id` NOT NULL | FK |
| applies | 1:N | application total | `application.member_id` NOT NULL | FK + UNIQUE(job, member) |
| receives | 1:N | application total | `application.job_id` NOT NULL | FK |
| schedules | 1:N | interview total | `interview.application_id` NOT NULL | FK + UNIQUE(app, round) + trigger |
| interviews | 1:N | interview total | `interview.interviewer_id` NOT NULL | FK |
| produced_by | 1:1 | referral total | `referral.application_id` NOT NULL UNIQUE | UNIQUE + trigger |
| refers | 1:N | referral total | `referral.referrer_id` NOT NULL | FK + trigger |
| connects | M:N | partial | `connection(member_a_id, member_b_id)` | PK + CHECK(a < b) |

---

## 3. Referential actions, and why they differ

| Child table | Parent | ON DELETE | ON UPDATE | Reason |
|---|---|---|---|---|
| `job_posting` | `company` | CASCADE | CASCADE | A company that is removed takes its postings with it. |
| `job_posting` | `member` (recruiter) | RESTRICT | CASCADE | Deleting a recruiter would orphan live postings; the account is closed, not deleted. |
| `application` | `job_posting`, `member` | CASCADE | CASCADE | An application has no meaning without its posting or its candidate. |
| `interview` | `application` | CASCADE | CASCADE | Rounds belong to the application. |
| `interview` | `member` (interviewer) | RESTRICT | CASCADE | The record of who assessed whom is evidence; it must not vanish with the account. |
| `referral` | `application` | CASCADE | CASCADE | 1:1 dependent. |
| `referral` | `member` (referrer) | RESTRICT | CASCADE | Bonus accountability. |
| `member_skill`, `education`, `experience`, `connection` | `member` | CASCADE | CASCADE / RESTRICT | Profile parts die with the profile, except `experience.member_id` where the generated column forbids ON UPDATE CASCADE. |
| `member_skill`, `job_skill` | `skill` | CASCADE | CASCADE | Removing a vocabulary term removes the claims that used it. |

The two RESTRICT choices are deliberate: **history that attributes a decision to a person
is retained**, while **content that belongs to an entity is deleted with it**.

---

## 4. Integrity constraints, grouped

| Class | Count | Examples |
|---|---|---|
| Primary keys | 12 | every relation |
| Unique constraints | 7 | `uk_member_email`, `uk_company_name`, `uk_skill_name`, `uk_app_job_member`, `uk_int_app_round`, `uk_ref_application`, `uk_exp_one_current` |
| Foreign keys | 17 | see §3 |
| CHECK constraints | 25 | salary band, score range, canonical edge order, `decided_at ≥ applied_at`, … |
| Triggers | 4 | status machine, interview eligibility, referral validity, insert-time state consistency |
| Application rules | 3 | no self-application to current employer, no application to DRAFT, hires ≤ openings (enforced by the seed and audited by `_consistency_report.json`) |

`Constraint_Inventory.md` maps every numbered business rule to exactly one of these, with
the failing statement that demonstrates it.
