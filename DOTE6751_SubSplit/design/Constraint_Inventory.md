# SubSplit — Constraint Inventory

Every rule the business depends on, where it is enforced, and what happens when someone
breaks it. "Type" follows the classical split: entity integrity, referential integrity,
domain integrity, user-defined (business) integrity.

## 1. Entity integrity (primary keys)

| ID | Rule | Object | Enforced by | On violation |
|---|---|---|---|---|
| C-01 | Every row is identifiable | all 11 tables | PRIMARY KEY | duplicate key error 1062 |
| C-02 | A member holds at most one seat per group | `membership_seat` | `uk_seat_group_member (group_id, member_id)` | error 1062 |
| C-03 | An escrow belongs to exactly one seat | `escrow_payment.seat_id` | `uk_escrow_seat` | error 1062 |
| C-04 | A month is released at most once per escrow | `monthly_payout_log` | `uk_payout_escrow_month (escrow_id, release_month)` | error 1062 |
| C-06 | A product is defined once | `digital_service` | `uk_service (brand, region, plan_name)` | error 1062 |
| C-07 | A payment instrument is registered once | `payment_method` | `uk_pm_user_account` | error 1062 |


> C-05 was removed together with the `email` column: the field was dropped from the design
> because a synthetic instance cannot carry a believable institutional address. Numbering is
> kept as-is so that cross-references elsewhere in this document stay valid.

## 2. Referential integrity (foreign keys)

| ID | Rule | Object | Action |
|---|---|---|---|
| C-08 | A group must have a real host | `carpool_group.host_id → app_user` | RESTRICT |
| C-09 | A group must sell a real product | `carpool_group.service_id → digital_service` | RESTRICT |
| C-10 | A seat needs a group and a member | `membership_seat` | CASCADE / RESTRICT |
| C-11 | A credential needs its group | `credential_vault.group_id` | CASCADE |
| C-12 | An escrow needs its seat | `escrow_payment.seat_id` | CASCADE |
| C-13 | A payout needs its escrow | `monthly_payout_log.escrow_id` | CASCADE |
| C-14 | A complaint needs its seat | `dispute.seat_id` | CASCADE |
| C-15 | A credit event needs its user | `credit_event.user_id` | CASCADE |
| C-16 | A reviewer may be deleted without losing the dispute | `dispute.reviewer_id` | SET NULL |

**Why RESTRICT on C-08/C-09:** deleting a host or a product that still carries live money
would orphan the escrow. The platform must close the group first. This is a deliberate
choice, not a default.

## 3. Domain integrity

| ID | Rule | Object | Enforced by |
|---|---|---|---|
| C-17 | Credit score is between 0 and 100 | `app_user.credit_score` | `ck_user_credit` |
| C-18 | Seat price is positive | `carpool_group.seat_price` | `ck_group_price` |
| C-19 | Official price is positive | `digital_service.official_monthly_price` | `ck_service_price` |
| C-20 | Seat ceiling is 2–6 | `digital_service.max_seats` | `ck_service_seats` |
| C-21 | A seat expires after it starts | `membership_seat` | `ck_seat_window` |
| C-22 | Prepayment is positive | `escrow_payment.total_prepaid` | `ck_escrow_positive` |
| C-23 | Escrow balance identity holds | `escrow_payment` | `ck_escrow_balance` (remaining = total − released, 0 ≤ released ≤ total) |
| C-24 | Payout amount is positive and the fee is smaller than it | `monthly_payout_log` | `ck_payout_amount`, `ck_payout_fee` |
| C-25 | Credit delta is within ±100 and the score stays in range | `credit_event` | `ck_credit_delta`, `ck_credit_after` |
| C-26 | Enumerated states are closed sets | every ENUM column | column type |

## 4. User-defined (business) integrity

| ID | Rule | Enforced by | On violation |
|---|---|---|---|
| C-27 | Seats sold never exceed the product's ceiling | trigger `trg_seat_capacity` | SQLSTATE 45000 "seat capacity exceeded for this service" |
| C-28 | No new seat in a FROZEN or CLOSED group | trigger `trg_seat_capacity` | SQLSTATE 45000 "group is not open for new seats" |
| C-29 | A user has at most one default payment instrument | triggers `trg_default_payment_ins` / `_upd` | previous default is cleared automatically |
| C-30 | Every credential change is journalled | trigger `trg_password_log` | log row written in the same transaction |
| C-31 | The escrow balance follows the ledger | trigger `trg_escrow_after_payout` + C-23 | update refused if identity breaks |
| C-32 | Only an administrator reviews a dispute | application layer, backed by `app_user.account_role` | rejected by the service layer; audit kept in `dispute.reviewer_id` |
| C-33 | A dispute cannot go from OPEN straight to REFUNDED without a reviewer | application layer (state machine) | transition refused |
| C-34 | Money is frozen while a dispute is live | application layer sets `escrow_status = 'FROZEN'` | payouts blocked, status visible in `v_escrow_balance` |

## 5. Division of labour, and why

| Layer | What it is good at | Rules placed there |
|---|---|---|
| Declarative DDL | cheap, engine-enforced, survives any client | keys, foreign keys, ranges, cross-column arithmetic |
| Triggers | row-level business logic that must hold for *every* writer | capacity, default instrument, credential journal, balance |
| Application | decisions that need a user identity, a workflow, or an external call | who may review, which transition is legal, when to freeze |

The rule of thumb: **if a rule must survive a careless `INSERT` from Navicat, it belongs in
the database.** C-27 to C-31 are exactly that case; C-32 and C-33 are not, because they
depend on *who* is acting, not only on the data.
