# Constraint Inventory

**LinkedIn, reverse-engineered · DOTE 6751 · November 2026**

A constraint that only exists in a document is a wish. This inventory maps every
business rule of `Requirements.md` to the database object that refuses to break it, and
then demonstrates the refusal. The demonstrations in §4 were executed against the loaded
database; `build/fault_injection.py` reproduces them and the captured messages are quoted
verbatim.

Enforcement vocabulary:

- **PK / UQ / FK / CK** — declarative MySQL 8.0 constraints (`01_schema.sql`).
- **TRG** — a trigger that can see more than one row or one table (`04_views_triggers.sql`).
- **SEED** — an invariant maintained by the data generator because SQL cannot express it
  cheaply; audited by `build/verify_data.py` on every rebuild.
- **APP** — a rule the product enforces in application code; recorded here so the reader
  knows it is *not* in the database.

---

## 1. Constraint surface

| Object type | Count | Names |
|---|---|---|
| Primary key | 12 | one per table |
| Unique key | 7 | `uk_company_name`, `uk_member_email`, `uk_skill_name`, `uk_app_job_member`, `uk_int_app_round`, `uk_ref_application`, `uk_exp_one_current` |
| Foreign key | 17 | `fk_job_*`, `fk_ms_*`, `fk_js_*`, `fk_app_*`, `fk_int_*`, `fk_ref_*`, `fk_edu_*`, `fk_exp_*`, `fk_conn_*` |
| CHECK | 25 | enumerated in §2 |
| Trigger | 4 | `trg_application_before_insert`, `trg_application_status_guard`, `trg_interview_before_insert`, `trg_referral_before_insert` |
| View | 4 | `v_member_current_employer`, `v_open_job_card`, `v_job_funnel`, `v_skill_demand_supply` |

Verified with:

```sql
SELECT COUNT(*) FROM information_schema.referential_constraints
 WHERE constraint_schema = 'linkedin_db';          -- 17
SELECT COUNT(*) FROM information_schema.check_constraints
 WHERE constraint_schema = 'linkedin_db';          -- 25
```

---

## 2. Rule-by-rule mapping

### 2.1 Company and member

| ID | Business rule | Enforced by | Object |
|---|---|---|---|
| BR-01 | A company name is unique | UQ | `uk_company_name` |
| BR-02 | A company cannot be founded in the future | CK | `ck_company_founded` (1700–2026) |
| BR-03 | `is_verified` is a flag, not a rating | CK | `ck_company_verified` |
| BR-04 | A member e-mail is unique | UQ | `uk_member_email` |
| BR-05 | Experience is at most 50 years | CK | `ck_member_years` |
| BR-06 | Visibility is one of three values | ENUM + CK | `ck_member_visibility` |

### 2.2 Posting and skill

| ID | Business rule | Enforced by | Object |
|---|---|---|---|
| BR-07 | A posting always belongs to a company and a recruiter | FK NOT NULL | `fk_job_company`, `fk_job_recruiter` |
| BR-08 | Salary band is ordered and positive | CK | `ck_job_salary` |
| BR-09 | Minimum experience ≤ 40 years; openings 1–50 | CK | `ck_job_years`, `ck_job_openings` |
| BR-10 | A posting closes no earlier than it opened | CK | `ck_job_closed` |
| BR-11 | A skill name is unique | UQ | `uk_skill_name` |
| BR-12 | Proficiency is 1–5; years 0–40; endorsements 0–999 | CK ×3 | `ck_ms_proficiency`, `ck_ms_years`, `ck_ms_endorse` |
| BR-13 | Every posting asks for 3–5 skills and at least three of them are hard requirements | SEED + audit | generator pass; `job_skill` count per posting |
| BR-14 | A skill cannot be both REQUIRED and PREFERRED on the same posting | PK | `PRIMARY KEY (job_id, skill_id)` |

### 2.3 Application, interview, referral

| ID | Business rule | Enforced by | Object |
|---|---|---|---|
| BR-15 | One application per member per posting | UQ | `uk_app_job_member` |
| BR-16 | An application always has a posting and a candidate | FK NOT NULL | `fk_app_job`, `fk_app_member` |
| BR-17 | Terminal status ⇔ `decided_at` present | CK (CHECK does not fire on status logic alone) + TRG | `ck_app_status`, `trg_application_before_insert`, `trg_application_status_guard` |
| BR-18 | `decided_at ≥ applied_at` | CK | `ck_app_decided` |
| BR-19 | Legal transitions only; job and candidate are immutable | TRG | `trg_application_status_guard` |
| BR-20 | Rounds are 1..n, unique per application | UQ + TRG | `uk_int_app_round`, `trg_interview_before_insert` |
| BR-21 | An interview exists only after the application reached the interview stage | TRG | `trg_interview_before_insert` |
| BR-22 | An interview is scheduled after the application date | TRG | `trg_interview_before_insert` |
| BR-23 | Score is 1–5 and is present exactly for PASS/FAIL | CK ×2 | `ck_int_score`, `ck_int_score_outcome` |
| BR-24 | A referral exists only for a REFERRAL application | TRG | `trg_referral_before_insert` |
| BR-25 | A referrer works at the hiring company, and is not the candidate | TRG | `trg_referral_before_insert` |
| BR-26 | A referral is 1:1 with its application | UQ | `uk_ref_application` |
| BR-27 | Bonus is never negative | CK | `ck_ref_bonus` |

### 2.4 Social graph and history

| ID | Business rule | Enforced by | Object |
|---|---|---|---|
| BR-28 | One live position per member | UQ on generated column | `uk_exp_one_current` |
| BR-29 | A current position has no end date; a past one must have one | CK | `ck_exp_current_open` |
| BR-30 | End date never precedes start date (experience and education) | CK ×2 | `ck_exp_dates`, `ck_edu_years` |
| BR-31 | An edge is stored once, in canonical order | PK + CK | `PRIMARY KEY (member_a_id, member_b_id)`, `ck_conn_order` |
| BR-32 | A member cannot interview themselves | APP + SEED | generator excludes the candidate; not a DB rule (see §5) |
| BR-33 | Hires per posting ≤ openings | SEED + audit | `_consistency_report.json` check I5 |
| BR-34 | No application to a DRAFT posting | TRG-adjacent: `trg_application_before_insert` reads the posting; the DRAFT case is audited as I16 | audit |
| BR-35 | No application to the current employer | APP + audit | audit check I13 |
| BR-36 | Deleting a person who has attributed decisions is refused | FK RESTRICT | `fk_int_member`, `fk_ref_member`, `fk_job_recruiter` |

---

## 3. The four triggers, and why a CHECK was not enough

| Trigger | Rule it carries | Why declarative DDL fails |
|---|---|---|
| `trg_application_before_insert` | terminal status requires `decided_at`; open status forbids it; `applied_at` after `posted_at` | `posted_at` lives in another table |
| `trg_application_status_guard` | legal transition map; `job_id`/`member_id` immutable; auto-stamp `decided_at` | a CHECK cannot compare OLD and NEW |
| `trg_interview_before_insert` | the application must be in a post-screening state; rounds must be contiguous; schedule after application | three facts from two other tables, plus `MAX(round_no)` |
| `trg_referral_before_insert` | channel must be REFERRAL; referrer must be employed by the hiring company; no self-referral | the candidate is only reachable through `application`, the employer through `experience` |

All four are `BEFORE` triggers and `SIGNAL SQLSTATE '45000'`, so a violation surfaces as
error 1644 with a message a human can act on, rather than a generic constraint failure.

---

## 4. Fault injection — the proof

Run `build/fault_injection.py`. Each statement executes in its own transaction and is
rolled back; the database is byte-identical afterwards. Captured output:

| # | Injected fault | Error | Message |
|---|---|---|---|
| F1 | apply twice to the same posting | 1062 | `Duplicate entry '34-259' for key 'application.uk_app_job_member'` |
| F2 | inverted salary band | 3819 | `Check constraint 'ck_job_salary' is violated.` |
| F3 | second current experience | 1062 | `Duplicate entry '1' for key 'experience.uk_exp_one_current'` |
| F4 | self-loop connection | 3819 | `Check constraint 'ck_conn_order' is violated.` |
| F5 | application to a non-existent posting | 1644 | `application: unknown job_id` |
| F6 | decision before application | 3819 | `Check constraint 'ck_app_decided' is violated.` |
| F7 | interview score 9 | 3819 | `Check constraint 'ck_int_score' is violated.` |
| F8 | HIRED without `decided_at` | 1644 | `application: a final status requires decided_at` |
| F9 | SUBMITTED → HIRED jump | 1644 | `application: illegal status transition` |
| F10 | interview scheduled before the application | 1644 | `interview: scheduled before the application date` |
| F11 | referral on a DIRECT application | 1644 | `referral: the application is not flagged as a referral` |
| F12 | referrer outside the hiring company | 1644 | `referral: the referrer does not work at the hiring company` |
| F13 | delete an interviewer | 1451 | `Cannot delete or update a parent row: a foreign key constraint fails (… fk_int_member …)` |
| F14 | negative bonus | 3819 | `Check constraint 'ck_ref_bonus' is violated.` |

14 of 14 faults were refused; `SELECT COUNT(*) FROM application` returned 250 before and
after, which is the evidence that the injections did not leak into the data.

---

## 5. Rules that are deliberately *not* in the database

| Rule | Where it lives | Why |
|---|---|---|
| No self-application to the current employer | seed + audit I13 | A trigger would have to read `experience` on every insert; the product blocks it at the UI, and the audit proves the seed respects it |
| Hires ≤ openings | seed + audit I5 | Enforcing it in a trigger would make the legal transition OFFER → HIRED depend on a count over another table on every write; batch and reporting workloads would pay for it |
| No application to a DRAFT posting | `trg_application_before_insert` reads the posting but only checks existence and date; the DRAFT rule is audited (I16) | Keeping the trigger to two facts made it readable; the audit covers the rest |
| A member may not interview themselves | generator | Same reasoning as BR-32; a CHECK cannot join |

Each of these is listed again in `Design_Rationale.md` §7 as a known trade-off, not an
oversight.
