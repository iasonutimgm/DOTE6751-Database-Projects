# Entity–Relationship Catalog

**LinkedIn, reverse-engineered · DOTE 6751 · November 2026**

This catalogue is the bridge between the Chen diagram (`erd/ERD_conceptual`) and the
relational schema (`design/Relational_Schema.md`). Every entity set is listed with its
attributes and identifier; every relationship set is listed with its participating
entity sets, cardinality, participation constraint and the relation that implements it.
Notation follows Silberschatz et al., *Database System Concepts*, 7th ed., Chapter 6:
`1` and `N` are the cardinality ratios of §6.2, "total" means every entity of that set
must participate (§6.3), and the reduction rules are those of §6.7.

---

## 1. Entity sets

### E1 · company

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `company_id` | INT, auto-increment | no | **identifier** |
| `company_name` | VARCHAR(90) | no | unique; the only natural key |
| `industry` | VARCHAR(60) | no | indexed; 18 values in the seed |
| `hq_country` | CHAR(2) | no | ISO-3166 alpha-2 |
| `size_band` | ENUM, 7 bands | no | head-count band, not an exact count |
| `founded_year` | SMALLINT | yes | 1700–2026 |
| `is_verified` | BOOLEAN | no | the product's page badge |

*Identifier:* `company_id`. *Participation:* total in **advertises** only when the company
has at least one posting; the seed leaves 0 companies without a posting.

### E2 · member

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `member_id` | INT, auto-increment | no | **identifier** |
| `full_name` | VARCHAR(80) | no | display name |
| `headline` | VARCHAR(140) | yes | free text, a snapshot rather than a derived fact |
| `email` | VARCHAR(120) | no | unique |
| `country`, `city` | CHAR(2), VARCHAR(60) | no | location |
| `years_experience` | TINYINT UNSIGNED | no | 0–50 |
| `open_to_work` | BOOLEAN | no | the product's green banner |
| `profile_visibility` | ENUM(PUBLIC, CONNECTIONS, PRIVATE) | no | |
| `joined_at` | DATE | no | |

*Identifier:* `member_id`. *Participation:* total in **claims** (a profile with no skill
would be invisible to the matching queries), partial in **studied** and **worked**.

### E3 · job_posting

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `job_id` | INT, auto-increment | no | **identifier** |
| `company_id` | INT | no | FK → company |
| `recruiter_id` | INT | no | FK → member, the poster |
| `title` | VARCHAR(120) | no | |
| `seniority` | ENUM, 7 levels | no | used to bucket cycle time (Q10, Q15) |
| `employment_type` | ENUM, 4 values | no | |
| `work_mode` | ENUM(ONSITE, HYBRID, REMOTE) | no | |
| `city`, `country` | VARCHAR(60), CHAR(2) | no | |
| `salary_min`, `salary_max` | INT | no | annual, `max ≥ min > 0` |
| `currency` | CHAR(3) | no | default 'USD' |
| `min_years_experience` | TINYINT UNSIGNED | no | |
| `openings` | TINYINT UNSIGNED | no | 1–50, bounded by a CHECK |
| `status` | ENUM(DRAFT, OPEN, CLOSED, ON_HOLD) | no | lifecycle |
| `posted_at`, `closed_at` | DATETIME | no / yes | `closed_at ≥ posted_at` |

*Identifier:* `job_id`. *Participation:* total in **advertises** (every posting has a
company) and **receives** (a posting with no application is legal only for DRAFT/ON_HOLD,
a rule the seed respects).

### E4 · skill

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `skill_id` | INT, auto-increment | no | **identifier** |
| `skill_name` | VARCHAR(60) | no | unique; 60-entry controlled vocabulary |
| `skill_family` | ENUM, 8 families | no | LANGUAGE, FRAMEWORK, DATABASE, CLOUD, DATA, PRODUCT, DESIGN, SOFT |
| `is_emerging` | BOOLEAN | no | flags skills with thin proven supply (Q17) |

*Identifier:* `skill_id`. *Participation:* total in **held_as** and **asked_as** in
practice; partially in the model (an unused skill may exist).

### E5 · member_skill — associative entity of **claims**

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `member_id` | INT | no | **partial identifier**, FK → member |
| `skill_id` | INT | no | **partial identifier**, FK → skill |
| `proficiency` | TINYINT | no | 1–5 |
| `years_used` | DECIMAL(3,1) | no | 0–40 |
| `endorsement_count` | SMALLINT | no | 0–999 |
| `added_at` | DATE | no | |

*Identifier:* the pair (`member_id`, `skill_id`). The attributes describe the *claim*,
not the member and not the skill, which is exactly why this relation is in 3NF without
decomposition (§6.7.3 applied to a relationship set with descriptive attributes).

### E6 · job_skill — associative entity of **requires** / **asked_as**

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `job_id` | INT | no | **partial identifier**, FK → job_posting |
| `skill_id` | INT | no | **partial identifier**, FK → skill |
| `importance` | ENUM(REQUIRED, PREFERRED) | no | drives every gap query |
| `min_proficiency` | TINYINT | no | 1–5 |

*Identifier:* (`job_id`, `skill_id`). `importance` cannot migrate to either parent: the
same skill is REQUIRED for one posting and PREFERRED for another.

### E7 · application — associative entity of **applies**

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `application_id` | INT, auto-increment | no | **identifier** (surrogate) |
| `job_id` | INT | no | FK → job_posting |
| `member_id` | INT | no | FK → member |
| `source_channel` | ENUM(DIRECT, REFERRAL, SOURCING) | no | how the candidate arrived |
| `status` | ENUM, 7 states | no | the state machine of §2.7 |
| `applied_at` | DATETIME | no | |
| `decided_at` | DATETIME | yes | set exactly for terminal states |
| `resume_version` | VARCHAR(20) | no | which CV was sent |

*Identifier:* `application_id`. A natural key (`job_id`, `member_id`) also exists and is
enforced as `UNIQUE`, so the two candidate keys agree.

### E8 · interview

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `interview_id` | INT, auto-increment | no | **identifier** |
| `application_id` | INT | no | FK → application |
| `round_no` | TINYINT UNSIGNED | no | 1–6, unique per application |
| `interview_type` | ENUM(PHONE, VIDEO, ONSITE, TECHNICAL, HR) | no | |
| `scheduled_at` | DATETIME | no | |
| `duration_min` | SMALLINT UNSIGNED | no | 15–480 |
| `interviewer_id` | INT | no | FK → member |
| `outcome` | ENUM(PENDING, PASS, FAIL, NO_SHOW) | no | |
| `score` | TINYINT | yes | 1–5, required for PASS/FAIL |

*Identifier:* `interview_id`; business key (`application_id`, `round_no`), enforced unique.

### E9 · referral

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `referral_id` | INT, auto-increment | no | **identifier** |
| `application_id` | INT | no | FK → application, **unique** (1:1) |
| `referrer_id` | INT | no | FK → member |
| `relationship` | ENUM, 5 values | no | COLLEAGUE … OTHER |
| `referred_at` | DATETIME | no | |
| `bonus_amount` | DECIMAL(10,2) | no | ≥ 0 |
| `bonus_status` | ENUM(NONE, PENDING, PAID, FORFEITED) | no | |

*Identifier:* `referral_id`. Because the candidate and the posting are functions of
`application_id`, storing them here would create a transitive dependency — see
`Normalization_Proof.xlsx`, sheet **referral**.

### E10 · education

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `education_id` | INT, auto-increment | no | **identifier** |
| `member_id` | INT | no | FK → member |
| `school_name` | VARCHAR(100) | no | |
| `degree` | ENUM, 6 levels | no | |
| `field_of_study` | VARCHAR(80) | no | |
| `start_year`, `end_year` | SMALLINT | no / yes | `end_year ≥ start_year` |

*Identifier:* `education_id`; (`member_id`, `school_name`, `degree`) is a natural key the
seed does not violate but the schema does not enforce — recorded as a known gap.

### E11 · experience

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `experience_id` | INT, auto-increment | no | **identifier** |
| `member_id` | INT | no | FK → member |
| `company_id` | INT | no | FK → company |
| `title` | VARCHAR(100) | no | |
| `start_date`, `end_date` | DATE | no / yes | |
| `is_current` | BOOLEAN | no | one per member, enforced by a generated-column unique index |
| `current_member_id` | INT, generated | yes | `IF(is_current, member_id, NULL)` |

*Identifier:* `experience_id`. The generated column is the portable MySQL 8.0 substitute
for the partial index `UNIQUE (member_id) WHERE is_current = 1`.

### E12 · connection

| Attribute | Domain | Null | Notes |
|---|---|---|---|
| `member_a_id` | INT | no | **partial identifier**, FK → member, `a < b` |
| `member_b_id` | INT | no | **partial identifier**, FK → member |
| `connected_at` | DATETIME | no | |
| `connection_type` | ENUM(COLLEAGUE, CLASSMATE, FRIEND, FOLLOW) | no | |

*Identifier:* the ordered pair. The ordering constraint is part of the identifier, not a
presentation choice: it is what makes the relation a *set* of undirected edges.

---

## 2. Relationship sets

| # | Relationship | Entity sets | Cardinality | Participation | Attributes | Implemented by |
|---|---|---|---|---|---|---|
| R1 | **advertises** | company → job_posting | 1 : N | company partial, posting total | — | `job_posting.company_id` |
| R2 | **employs** | company → experience | 1 : N | experience total | — | `experience.company_id` |
| R3 | **studied** | member → education | 1 : N | education total | — | `education.member_id` |
| R4 | **worked** | member → experience | 1 : N | experience total | `title`, `start_date`, `end_date`, `is_current` | `experience` table |
| R5 | **claims** | member → member_skill | 1 : N | member total | `proficiency`, `years_used`, `endorsement_count`, `added_at` | `member_skill` table |
| R6 | **held_as** | skill → member_skill | 1 : N | total | — | `member_skill.skill_id` |
| R7 | **requires** | job_posting → job_skill | 1 : N | job total | `importance`, `min_proficiency` | `job_skill` table |
| R8 | **asked_as** | skill → job_skill | 1 : N | total | — | `job_skill.skill_id` |
| R9 | **applies** | member → application | 1 : N | application total | `source_channel`, `status`, `applied_at`, `decided_at`, `resume_version` | `application` table |
| R10 | **receives** | job_posting → application | 1 : N | application total | — | `application.job_id` |
| R11 | **schedules** | application → interview | 1 : N | interview total | `round_no`, `interview_type`, `scheduled_at`, `duration_min`, `outcome`, `score` | `interview` table |
| R12 | **interviews** | member → interview | 1 : N | interview total | — | `interview.interviewer_id` |
| R13 | **produced_by** | application → referral | 1 : 1 | referral total, application partial | `relationship`, `referred_at`, `bonus_amount`, `bonus_status` | `referral.application_id` (UNIQUE) |
| R14 | **refers** | member → referral | 1 : N | referral total | — | `referral.referrer_id` |
| R15 | **connects** | member ↔ member | M : N (self) | partial both sides | `connected_at`, `connection_type` | `connection` table |

### Notes on the four non-obvious relationships

**R5 / R7 (multi-valued attributes promoted to relations).** "Skills a member claims" and
"skills a posting asks for" are multivalued attributes of member and posting. §6.2 of the
textbook models them as multivalued attributes; §6.7 materialises each as its own relation
whose key is the owning entity plus the value. We go one step further and attach
descriptive attributes (`proficiency`, `importance`), which is why they are associative
entities in the Chen diagram rather than plain value sets.

**R13 (1:1 with a mandatory referral side).** A referral cannot exist without the
application it produced, so the application identifier migrates into `referral` as both a
foreign key and a unique constraint. The alternative — a `referral_id` column on
`application` — would have been nullable for 76 % of applications and would have created a
second candidate key on the same relation; see `Design_Rationale.md` §3.

**R15 (self relationship).** A connection is undirected. Storing it as an ordered pair with
`CHECK (member_a_id < member_b_id)` halves the row count and makes "is A connected to B"
a single primary-key lookup regardless of the direction. The recursive query Q18 walks
this relation in both directions with an `IF()` that flips the pair.

**R12 (member as interviewer).** There is no separate interviewer entity: an interviewer is
a member, and the same member can be a candidate in another application. This is the
reason `interview.interviewer_id` references `member` rather than a role table.

---

## 3. What the model deliberately does not contain

| Absent | Why |
|---|---|
| Saved jobs, follows, post likes | Product surface without analytical value for the hiring loop |
| Recruiter notes / reject reasons | Not observable publicly; inventing them would be fiction, not reverse engineering |
| Offer / negotiation table | The offer is a state (`OFFER`) plus a decision timestamp; compensation is the posting's band |
| Stage-transition audit log | `decided_at` plus interview timestamps recover the cycle time for every query we need; a full log is listed as future work |
| Salary currency table | One currency in the seed; `currency` remains a column for correctness |

*Cross-references:* attribute domains and constraint names are enumerated one by one in
`Constraint_Inventory.md`; the reduction of each relationship set to a relation schema is
written out in `Relational_Schema.md` §2.
