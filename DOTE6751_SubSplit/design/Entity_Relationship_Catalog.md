# SubSplit — Entity and Relationship Catalogue

Reference model: Silberschatz, Korth & Sudarshan, *Database System Concepts*, Part 2,
Chapter 6 ("Database Design Using the E-R Model"). Notation follows §6.2–§6.4; the
mapping to relations follows §6.7.

Each relationship carries a **cardinality limit** `l..h` on both ends (§6.4), which is
stricter than a bare 1:N label: `1..1` means "exactly one", `0..*` means "zero or more".

---

## 1. Entity sets (11)

### 1.1 app_user — strong entity
A natural person with an account. `user_id` is the key. `account_role` separates ordinary
users from administrators; host/member are *behaviours*, inferred from whether the person
appears in `carpool_group.host_id` or `membership_seat.member_id`, not stored as a type.
`credit_score` is a derived-in-principle attribute (100 + Σ credit_event.delta) that is
stored for read speed and audited in `credit_event`.

### 1.2 payment_method — strong entity, existence-dependent on app_user
A funding instrument. `pm_id` is the key; `(user_id, masked_account)` is unique. The
"exactly one default per user" rule is a *constraint on a relationship*, not expressible as
a key, so it is enforced by trigger `trg_default_payment_*`.

### 1.3 digital_service — strong entity
The dictionary of products: brand, region, plan, official seat ceiling, official monthly
price. The key is `service_id`; `(brand, region, plan_name)` is a natural unique key. The
seat ceiling lives here because it is a property of the product, not of any one group.

### 1.4 carpool_group — strong entity
One host reselling seats of one service. `group_id` is the key. `full_at` records the
instant the last seat was taken — a derived-state timestamp that makes "time to fill"
answerable without replaying the seat table. `status` is a five-state lifecycle:
RECRUITING → FULL → ACTIVE, with FROZEN and CLOSED as terminal variants.

### 1.5 credential_vault — **weak entity**
The household credential (invite link, encrypted passphrase). It has no independent
identity: without its group it means nothing. Its discriminator is the owner's key, so
`group_id` is at once the primary key and the foreign key. This is the textbook weak-entity
case of §6.7.3, and it is deleted with its owner (`ON DELETE CASCADE`).

### 1.6 membership_seat — **associative entity** between app_user and carpool_group
The M:N relationship "a member occupies a seat in a group" carries its own attributes
(joined_at, expires_at, seat_status), so it is promoted to an entity (§6.9.3). Its key is
`seat_id`; `(group_id, member_id)` is unique, which is the "one seat per group per person"
rule.

### 1.7 escrow_payment — strong entity, 1:1 with a seat
The prepayment held on behalf of one seat. `seat_id` is unique, so the relationship to
`membership_seat` is 1:1. `total_prepaid`, `released_amount` and `remaining_amount` are
kept consistent by a CHECK constraint and by trigger `trg_escrow_after_payout`.

### 1.8 monthly_payout_log — strong entity, weak in spirit
The ledger of releases. `(escrow_id, release_month)` is unique, which makes double payment
of a month impossible. Rows are append-only; a blocked month is recorded, not deleted.

### 1.9 password_change_log — strong entity, existence-dependent on credential_vault
Append-only journal of credential changes. Needed because the vault only carries the latest
timestamp, while the risk query needs *how many* changes happened in a window.

### 1.10 dispute — strong entity with a state machine
A member's complaint about a seat. `dispute_status` moves OPEN → UNDER_REVIEW →
REFUNDED / REJECTED; `reviewed_at` and `reviewer_id` are NULL until an administrator acts.
Only administrators hold the reviewer role, which is what makes "manual review" meaningful.

### 1.11 credit_event — strong entity, existence-dependent on app_user
The audit trail of reputation. `delta`, `reason`, `score_after` make the score reproducible
and explainable; `ref_dispute_id` links a penalty back to the complaint that caused it.

---

## 2. Relationship sets (14)

| # | Relationship | Between | Cardinality (both ends) | Participation | Attributes | Notes |
|---|---|---|---|---|---|---|
| R1 | owns | app_user — payment_method | `1..1` — `0..*` | partial on instrument | — | A user may bind several instruments; one is default |
| R2 | earns | app_user — credit_event | `1..1` — `0..*` | total on event | — | Every score change leaves a row |
| R3 | hosts | app_user — carpool_group | `1..1` — `0..*` | total on group | — | `group.host_id` NOT NULL |
| R4 | sits in | app_user — membership_seat | `1..1` — `0..*` | total on seat | — | See R7 for the group side |
| R5 | reviews | app_user — dispute | `0..1` — `0..*` | partial | — | Only ADMIN users appear here |
| R6 | updated by | app_user — credential_vault | `0..1` — `0..*` | partial | — | Who last changed the passphrase |
| R7 | sold as | digital_service — carpool_group | `1..1` — `0..*` | total on group | — | A group sells exactly one product |
| R8 | secured by | carpool_group — credential_vault | `1..1` — `1..1` | total on vault | — | Weak entity: key borrowed from group |
| R9 | contains | carpool_group — membership_seat | `1..1` — `0..*` | total on seat | — | Ceiling enforced by trigger |
| R10 | prepaid by | membership_seat — escrow_payment | `1..1` — `1..1` | total on escrow | — | One escrow per seat |
| R11 | releases | escrow_payment — monthly_payout_log | `1..1` — `0..*` | total on log | release_month, amount, platform_fee | At most 12 rows per escrow |
| R12 | raises | membership_seat — dispute | `1..1` — `0..*` | total on dispute | opened_at, category | A seat may be complained about more than once |
| R13 | journals | credential_vault — password_change_log | `1..1` — `0..*` | total on log | changed_at, reason | Written by trigger |
| R14 | triggers | dispute — credit_event | `0..1` — `0..*` | partial | — | A penalty may cite its dispute |

---

## 3. Constraints that the diagram cannot express

| Constraint | Why not in the diagram | Where it lives |
|---|---|---|
| Seats taken ≤ service.max_seats | Aggregates over a set, not a per-row rule | trigger `trg_seat_capacity` |
| One default payment instrument per user | Partial uniqueness, unsupported by MySQL keys | triggers `trg_default_payment_ins/upd` |
| remaining = total − released | Cross-column arithmetic | CHECK `ck_escrow_balance` + trigger |
| A month paid once | Composite unique key | `uk_payout_escrow_month` |
| Only an admin may close a dispute | Depends on the actor's role, not on the row | application layer (documented in Constraint_Inventory) |
| Frozen group's money does not move | State-dependent | application layer + `escrow_status = 'FROZEN'` |

---

## 4. Cardinality limits in words

- **R8 / R10** are the only two `1..1 — 1..1` relationships: a group has exactly one
  credential, a seat has exactly one escrow. Both are enforced by making the foreign key
  the primary key (`credential_vault`) or unique (`escrow_payment.seat_id`).
- **R9 / R11 / R12 / R13** are `1..N` with total participation on the many side: a seat
  cannot exist without a group, a payout cannot exist without an escrow.
- **R1 / R5 / R6 / R14** are partial on at least one side: a user may never have filed a
  complaint, a dispute may never have produced a penalty.
