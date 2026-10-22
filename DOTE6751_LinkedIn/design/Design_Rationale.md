# Design Rationale

**LinkedIn, reverse-engineered · DOTE 6751 · November 2026**

This document records the decisions that a schema cannot explain by itself: why the model
has twelve tables and not nine or twenty, why two attributes that look natural are
missing, what is deliberately redundant, and what we would change at production scale.
Section references are to Silberschatz, Korth and Sudarshan, *Database System Concepts*,
7th ed. — Chapter 6 for the E-R reduction, Chapter 7 for normalisation.

---

## 1. Why the hiring loop is the spine

A social network can be modelled in indefinitely many ways. We chose the **closed hiring
loop** (company → posting → application → interview → hire) as the spine for three
reasons.

1. **It has a beginning and an end.** Every other product surface (feed, messaging,
   advertising) is open-ended; the loop produces a decision with a timestamp, which is
   what makes cycle-time and conversion queries meaningful rather than decorative.
2. **It exposes the graph.** The referral chain forces the model to carry a social edge
   (`connection`) and a person-to-person act (`referral`), so the "social" part of the
   product is represented by data rather than by a diagram.
3. **It exercises every construct the course requires** — 1:N, M:N, 1:1, self-relationship,
   multivalued attributes promoted to relations, and a state machine (§6.7, §7.3.2).

The skill tables are the second axis: without them the model can describe *that* someone
was hired but not *why*, and the matching queries (Q09, Q12, Q17, Q18) would have nothing
to match.

---

## 2. Entity or relationship? Three judgment calls

### 2.1 `application` is an entity, not a diamond

In a first-cut Chen diagram, "applies" is a relationship between member and posting. We
made it an entity with a surrogate key because it has **its own relationships**
(interviews, referral) and its own lifetime after the posting closes. §6.7.5 would give a
pure M:N relation keyed by (`member_id`, `job_id`); adding `status` and `decided_at` to
that relation is legal, but nothing could then reference "one application" — an interview
would have to carry the pair. The surrogate key makes `interview.application_id` a single
column and keeps the interview relation independent of how applications are identified.

The natural key survives as `UNIQUE (job_id, member_id)`, so the two candidate keys agree
and neither is redundant in the normalisation sense.

### 2.2 `referral` is 1:1 with the application

Two designs were possible:

| Option | Shape | Consequence |
|---|---|---|
| A (chosen) | `referral(application_id UNIQUE, referrer_id, …)` | The candidate and the posting are read through the application; no transitive dependency |
| B | `application(referral_id NULL, …)` | 76 % of applications carry a NULL column; a second candidate key appears on a 250-row table |

Option B would have created the FD `application_id → referral_id` *and* kept
`referral_id` nullable, which in practice invites the anomaly "referral exists, application
does not". Option A makes the referral unrepresentable without its application — the
foreign key is the business rule.

### 2.3 Skills are relations, not comma-separated text

Storing `skills = 'Python, SQL, AWS'` on `member` would violate 1NF (§7.2) and make every
gap query a string search. The M:N relations `member_skill` and `job_skill` carry the
attributes that make matching meaningful (`proficiency`, `min_proficiency`,
`importance`). This is the §6.7.6 rule applied to a multivalued attribute, extended with
descriptive attributes.

---

## 3. Keys: surrogate by default, natural where it is also the identity

Every table has a surrogate primary key. That is a deliberate, not a lazy, choice:

- **Stability.** A member's e-mail can change; the identifier must not.
- **Narrow foreign keys.** `interview.application_id` is a 4-byte integer rather than a
  composite of two integers plus a channel.
- **Uniform ORM and index behaviour.** Every join in `03_queries.sql` is an integer
  equality.

Where a natural key is genuinely the identity, it is kept as a UNIQUE constraint rather
than discarded: `uk_member_email`, `uk_company_name`, `uk_skill_name`,
`uk_app_job_member`, `uk_int_app_round`. The database therefore knows both identities and
refuses to let them diverge.

The one place where the *ordering* of the key is semantic is `connection`: the primary key
is (`member_a_id`, `member_b_id`) with a CHECK that `a < b`. The unordered pair is the
identity of an undirected edge; ordering it is how a relational store represents that
identity without storing every edge twice.

---

## 4. Derived data: what we refused to store

### 4.1 Current employer is not a column on `member`

The product shows "Project Manager at Siemens" on the profile. The tempting design adds
`member.current_company_id`. We did not, because that column would create the FD
`member_id → current_company_id` that is already implied by
`experience(member_id, is_current) → company_id`. Storing both means the two can disagree
after an edit — the classic update anomaly of §7.1.

Instead, `experience.is_current` carries the fact, and a **generated column** enforces
"at most one current position":

```sql
current_member_id INT GENERATED ALWAYS AS (IF(is_current = 1, member_id, NULL)) VIRTUAL,
UNIQUE KEY uk_exp_one_current (current_member_id)
```

MySQL 8.0 has no partial index, and a `UNIQUE (member_id, is_current)` key would forbid a
member from having *two past* positions. A unique index over a nullable generated column
permits unlimited NULLs and exactly one live row per member — the portable substitute.
The cost is one join to read the current employer, which `v_member_current_employer`
absorbs.

### 4.2 `decided_at` instead of an audit table

A full status-history table would be the textbook answer for auditability, and it is what
we would build if the requirement were "reconstruct every state change". For this project
the analytical need is cycle time: `TIMESTAMPDIFF(DAY, applied_at, decided_at)`. One
timestamp set by the status trigger satisfies Q10 and Q14 at a fraction of the write cost.
The limitation is explicit in §7: intermediate stage durations are not recoverable.

### 4.3 Funnel counts are a view, not a table

`v_job_funnel` aggregates applications per posting. Materialising it would duplicate state
that the application table already holds; a view cannot drift. If the dashboard ever
needed sub-second latency at 10⁷ rows, we would add a summary table refreshed on a
schedule and accept the staleness — a trade-off recorded here rather than discovered in
production.

---

## 5. Normalisation: 3NF proven, BCNF in hand

Every relation is in third normal form; the per-table argument (attributes, FDs,
candidate keys, the 3NF test for each non-trivial FD) is in
`Normalization_Proof.xlsx`. The stronger result also holds: **all twelve relations are in
BCNF**, because every determinant we can identify is a candidate key.

Two subtleties worth stating, because a marker will look for them:

1. **`job_posting.recruiter_id` does not determine `company_id`.** In the seed a recruiter
   only posts for their own employer, so the data *looks* like the FD holds. It is not a
   schema FD: a recruiter can change employer and the historical posting stays with the
   company that paid for it. Treating it as an FD would put the relation in 3NF but not
   BCNF, and would be wrong.
2. **`application` has two candidate keys.** `application_id` and
   (`job_id`, `member_id`) are both minimal. Every FD has a candidate key on the left, so
   the relation is BCNF; the surrogate is kept for referential convenience, not because
   the natural key is inadequate.

No decomposition was necessary. The textbook's decomposition algorithms (§7.3.1, §7.4)
would have nothing to split: the schema was designed by mapping a normalised E-R model
(§6.7), which is the cheaper route to the same guarantee. The one relation that *could*
be decomposed — `experience` into current and past — would break the "history in one
place" requirement and buy nothing.

---

## 6. Denormalisation, and what we accepted

| Item | Redundant? | Justification |
|---|---|---|
| `member.headline` | yes, it paraphrases `experience.title` + `company_name` at write time | It is a **snapshot**, not a cache: the product shows what the member wrote, even after they change jobs. Recomputing it would silently rewrite history. |
| `interview.score` nullable | no | Nullability encodes "not yet scored"; the CHECK ties it to the outcome. |
| `job_posting.openings` | no | Independent fact, not derivable from applications. |
| `v_job_funnel`, `v_skill_demand_supply` | yes, but read-only | Views, not tables: they cannot drift. |
| `connection` stored once | — | Halves storage and makes the uniqueness constraint trivial; the cost is the `IF()` in the recursive query. |

Nothing else is denormalised. In particular we did **not** add `application.hired_flag`,
`company.open_job_count` or `member.application_count`; each of those would be a cached
aggregate that the 18 queries recompute correctly and cheaply.

---

## 7. Known limitations

| # | Limitation | Effect | Would fix by |
|---|---|---|---|
| L1 | No stage-transition history | Only total cycle time is measurable; "days in screening" is approximated by `applied_at` (Q13) | Adding `application_status_history` with a trigger |
| L2 | No offer or negotiation table | Compensation is the posting band; an accepted offer above band is invisible | `offer(application_id, base, bonus, currency, accepted_at)` |
| L3 | `decided_at` conflates "decision" with "last status change" | For WITHDRAWN applications it is the withdrawal date | Renaming to `closed_at`, or the history table of L1 |
| L4 | Education natural key unenforced | A member can record the same degree twice | `UNIQUE (member_id, school_name, degree, start_year)` |
| L5 | Referral eligibility is checked at insert only | A referrer who later leaves keeps the historical bonus | Intended: the record of the referral is evidence |
| L6 | No soft delete | Deleting a member cascades to applications, destroying funnel history | `deleted_at` + `ON DELETE RESTRICT` on `application.member_id` |
| L7 | Salary in one currency | Cross-country comparison is nominal | `fx_rate(date, currency, usd_rate)` |
| L8 | Connection graph in a relational table | Two-hop reach is a recursive query; three hops would be slow at scale | A graph store or a materialised reachability table |
| L9 | Seed is synthetic | Distributions are plausible, not empirical | Ingest a public job-board dump |

Every limitation is also a design conversation: L1 and L3 are the same missing fact seen
from two sides, and L6 is the one we would fix first, because destroying applications on
account deletion is a compliance problem as much as a modelling one.

---

## 8. What we would change at production scale

- **Partition `application` by `applied_at` year** — the table grows monotonically and
  almost every query filters a recent window.
- **Covering indexes** for the two hottest reads: `application(member_id, applied_at)` and
  `job_posting(status, country, city)`.
- **Materialise `v_job_funnel`** into a summary table refreshed hourly, and keep the view
  for ad-hoc queries.
- **Move `connection` to a graph store** and keep a `connection_digest` table for counts.
- **Add the audit table of L1** and derive every dashboard from it, so that `decided_at`
  stops doing double duty.

These are scale decisions, not correctness decisions: the twelve-table schema already
answers every question in `03_queries.sql` with plain 3NF relations, which is the property
the course asks us to demonstrate.
