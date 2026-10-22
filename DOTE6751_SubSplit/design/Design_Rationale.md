# SubSplit — Design Rationale

Why the schema looks the way it does. Each section answers a question a grader is likely
to ask, and points at the textbook concept it rests on.

---

## 1. Why eleven tables and not seven

The first draft of the idea had seven: user, service, group, credential, seat, escrow,
payout. Seven cannot answer the questions the project itself asks:

| Question the platform must answer | Missing piece | Fix |
|---|---|---|
| "Which groups changed the passphrase 4 times in 30 days?" | the vault keeps only the *latest* timestamp | `password_change_log` |
| "Who complained, about which seat, and did an admin approve?" | nothing recorded the complaint | `dispute` + reviewer role |
| "How many instruments does this member have?" | one text field cannot hold several cards atomically | `payment_method` |
| "How long did it take to fill?" | the group knows when it started, not when it filled | `full_at` |
| "Why is this host's score 60?" | a number with no history is not auditable | `credit_event` |

Every added table is a *multivalued fact* or an *event* in the E-R sense (§6.7.2): the
thing that must be recorded is not a value of an entity but a history of occurrences.

## 2. The weak entity, and why it earned its place

`credential_vault` has no identity of its own — a passphrase without a group is meaningless.
Modelling it as a weak entity (§6.7.3) gives it `group_id` as primary key, which
simultaneously:

- enforces 1:1 with the group (a second vault for the same group would collide on the key);
- cascades the delete (close the group, the credential goes with it);
- keeps the foreign key honest (there is no vault row without a group row).

The alternative — a `vault_id` surrogate plus a `group_id` unique column — is equivalent in
power but adds an attribute that means nothing to the business. The weak-entity form is the
one the textbook prescribes, and it reads better on the diagram.

## 3. Which side of the relationship gets the foreign key

Following §6.7.4:

| Case | Rule | Instance |
|---|---|---|
| 1:N | key of the "one" side goes to the "many" side | `carpool_group.host_id`, `membership_seat.group_id` |
| M:N | a separate relation, keys of both sides compose it | promoted to `membership_seat` because it carries attributes |
| 1:1 | unique foreign key on either side | `escrow_payment.seat_id` (unique), `credential_vault.group_id` (PK) |

`membership_seat` is the interesting one: it is *conceptually* an M:N relationship, but it
has a lifecycle (joined, expires, leaving, left) and its own key. §6.9.3 ("entity sets
versus relationship sets") is exactly this decision, and promoting it to an entity is what
lets a seat be complained about, refunded and expired independently of the group.

## 4. The seat ceiling lives in the product, not in the group

A naive design copies `max_seats` into `carpool_group`. That produces the classic transitive
dependency `group_id → service_id → max_seats`: the group's capacity is not a fact about the
group, it is a fact about the product. Keeping it only in `digital_service` is what makes
the schema 3NF rather than "3NF with an exception".

The cost is that the capacity trigger must join `carpool_group` to `digital_service` on every
insert. That is a two-row lookup on a primary key — a fair price for not having two places
that can disagree.

## 5. Deliberately stored derived values (the one honest denormalisation)

Four values are computed in principle and stored in practice:

| Stored | Computable as | Why stored |
|---|---|---|
| `escrow_payment.released_amount` | `SUM(monthly_payout_log.amount)` | read on every member's dashboard |
| `escrow_payment.remaining_amount` | `total_prepaid − released_amount` | the number shown when a dispute opens |
| `app_user.credit_score` | `100 + SUM(credit_event.delta)` | sorted and filtered on every listing |
| `carpool_group.full_at` | `MAX(membership_seat.joined_at)` | the whole "time to fill" analysis |

This is not a violation of 3NF: no new determinant appears, so the relations stay in BCNF.
It is a **materialisation** decision, and the design pays for it with two guarantees:

1. a CHECK constraint makes the escrow identity a rule the engine enforces
   (`remaining = total − released`), so a hand-written `UPDATE` cannot corrupt it;
2. a trigger keeps the balance equal to the ledger, and query **Q11** audits the equality
   for every escrow — the audit returns 0 rows when the system is healthy.

If the platform ever needed to rebuild from the ledger alone, one statement restores every
balance; that statement is part of `02_seed.sql` and is documented in the verification guide.

## 6. Manual review, not automatic refunds

An automatic rule ("two complaints ⇒ refund") is easy to write and wrong: two coordinated
friends could drain any host. The design therefore splits the decision:

- the **database** records and constrains the facts (a dispute exists, a reviewer, a
  timestamp, a frozen balance);
- the **administrator** makes the judgement, and the state machine
  `OPEN → UNDER_REVIEW → REFUNDED / REJECTED` makes the judgement visible.

The risk query (Q05) does not refund anything: it produces the *queue* a human should look
at — groups with three or more credential changes and two or more "cannot log in"
complaints in thirty days. That is the honest division between detection and decision.

## 7. Why the ledger, not a balance column alone

`monthly_payout_log` is append-only and keyed by `(escrow_id, release_month)`. This gives
three properties for free:

- **idempotence**: running the monthly job twice cannot pay twice (unique key);
- **auditability**: every dollar released has a row, a month, a fee and a status;
- **reversibility**: a blocked month is a new status, never a deletion.

The balance columns are a cache over this ledger, not a replacement for it.

## 8. Design alternatives considered and rejected

| Alternative | Why rejected |
|---|---|
| Subscription as an attribute of the group ("plan = Netflix HK") | duplicates product data across 60 groups; kills the price-comparison query |
| One `payment` table holding both prepayments and payouts | two different lifecycles (a hold vs a release) in one table; every query filters half of it away |
| `user.role` = HOST/MEMBER | a person is usually both; role would have to be duplicated or changed on the fly |
| Storing the plaintext passphrase | a database is not a secrets manager; the column is modelled as encrypted text and the platform never displays it |
| Refund as a negative payout row | a refund is not a release; mixing them breaks the `remaining = total − released` identity |
| Auto-refund on complaint count | gameable; see §6 |

## 9. What the design still cannot do

- It cannot verify that the host's bill is genuine; that is an external check (modelled as
  `credential_vault.verified_at`, populated by a process outside the database).
- It cannot stop a host from changing the password and lying about it; it can only make the
  change visible (`password_change_log`) and freeze the money (`escrow_status`).
- It does not model partial months. A member who leaves on day 20 of a month still receives
  the full twelfth for that month; the business accepts this simplification (A1).
- Regional pricing is modelled with a `currency` column but no exchange rates; comparisons
  across regions in Q07 are made within a region.

## 10. Textbook mapping

| Design decision | Reference |
|---|---|
| Entity / relationship / attribute modelling, cardinality limits `l..h` | Ch.6 §6.2–§6.4 |
| Weak entity `credential_vault` | Ch.6 §6.7.3 |
| 1:N, M:N, 1:1 mapping rules | Ch.6 §6.7.4 |
| Promotion of a relationship to an entity | Ch.6 §6.9.3 |
| Functional dependencies, candidate keys, 3NF/BCNF | Ch.7 §7.2–§7.3 |
| Lossless decomposition (not needed here, argued anyway) | Ch.7 §7.1.2 |
| Materialised derived values | Ch.7 §7.1 (redundancy vs performance trade-off) |
