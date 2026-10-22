# SubSplit — Relational Schema

Translation of the E-R design into relations, following Silberschatz §6.7:

- §6.7.1 strong entity sets → one relation each, entity key becomes primary key;
- §6.7.2 composite attributes flattened, multivalued attributes get their own relation;
- §6.7.3 weak entity sets → relation whose primary key includes the owner's key;
- §6.7.4 relationship sets → 1:N handled by a foreign key on the many side, M:N by a
  separate relation, 1:1 by a unique foreign key;
- §6.7.6 combination of schemas — not used: no two relations here share a key with an
  identical meaning, so merging would reintroduce redundancy.

Notation: **bold** = primary key, *italic* = foreign key, `UQ` = unique.

---

## 1. Relations

### R1 app_user
**app_user**(**user_id**, display_name, account_role, occupation, school,
credit_score, status, joined_at)

Source: strong entity `app_user` (§6.7.1).

### R2 payment_method
**payment_method**(**pm_id**, *user_id*, method_type, masked_account, is_default, created_at)
with `UQ(user_id, masked_account)`.

Source: strong entity + 1:N relationship R1; the foreign key lives on the many side
(§6.7.4, case 1:N).

### R3 digital_service
**digital_service**(**service_id**, brand, region, plan_name, max_seats,
official_monthly_price, currency) with `UQ(brand, region, plan_name)`.

Source: strong entity (§6.7.1) with a natural key added as a unique constraint.

### R4 carpool_group
**carpool_group**(**group_id**, *host_id*, *service_id*, status, seat_price, created_at,
full_at, closed_at)

Source: strong entity; two 1:N relationships (R3 hosts, R7 sold as) collapse into two
foreign keys on this side (§6.7.4).

### R5 credential_vault
**credential_vault**(**group_id**, invite_url, encrypted_passphrase, password_updated_at,
verified_at, *updated_by*)

Source: **weak entity** (§6.7.3). The owner's key `group_id` is borrowed as the primary key,
which also makes the relationship 1:1 without a separate relation.

### R6 membership_seat
**membership_seat**(**seat_id**, *group_id*, *member_id*, joined_at, expires_at,
seat_status) with `UQ(group_id, member_id)`.

Source: **M:N relationship promoted to an entity** because it carries attributes
(§6.7.4 for the M:N case, §6.9.3 for the promotion).

### R7 escrow_payment
**escrow_payment**(**escrow_id**, *seat_id* `UQ`, total_prepaid, released_amount,
remaining_amount, escrow_status, created_at)

Source: 1:1 relationship R10, implemented as a unique foreign key (§6.7.4, case 1:1).

### R8 monthly_payout_log
**monthly_payout_log**(**payout_id**, *escrow_id*, release_month, amount, platform_fee,
payout_status, settled_at) with `UQ(escrow_id, release_month)`.

Source: 1:N relationship R11; `release_month` is a relationship attribute that survives
into the relation.

### R9 password_change_log
**password_change_log**(**log_id**, *group_id*, changed_at, *changed_by*, reason)

Source: 1:N relationship R13. It exists because the vault stores only the latest timestamp;
the history is a **multivalued fact** in the E-R sense and therefore earns its own relation
(§6.7.2, the multivalued-attribute rule).

### R10 dispute
**dispute**(**dispute_id**, *seat_id*, category, detail, dispute_status, opened_at,
reviewed_at, *reviewer_id*, resolution_note)

Source: strong entity plus two 1:N relationships (R12 raises, R5 reviews).

### R11 credit_event
**credit_event**(**event_id**, *user_id*, delta, reason, *ref_dispute_id*, score_after,
created_at)

Source: 1:N relationship R2 plus the optional R14 link back to the dispute.

---

## 2. Foreign keys at a glance

| Relation | Column | References | On delete | On update |
|---|---|---|---|---|
| payment_method | user_id | app_user.user_id | CASCADE | CASCADE |
| carpool_group | host_id | app_user.user_id | RESTRICT | CASCADE |
| carpool_group | service_id | digital_service.service_id | RESTRICT | CASCADE |
| credential_vault | group_id | carpool_group.group_id | CASCADE | CASCADE |
| credential_vault | updated_by | app_user.user_id | SET NULL | CASCADE |
| membership_seat | group_id | carpool_group.group_id | CASCADE | CASCADE |
| membership_seat | member_id | app_user.user_id | RESTRICT | CASCADE |
| escrow_payment | seat_id | membership_seat.seat_id | CASCADE | CASCADE |
| monthly_payout_log | escrow_id | escrow_payment.escrow_id | CASCADE | CASCADE |
| password_change_log | group_id | credential_vault.group_id | CASCADE | CASCADE |
| password_change_log | changed_by | app_user.user_id | SET NULL | CASCADE |
| dispute | seat_id | membership_seat.seat_id | CASCADE | CASCADE |
| dispute | reviewer_id | app_user.user_id | SET NULL | CASCADE |
| credit_event | user_id | app_user.user_id | CASCADE | CASCADE |
| credit_event | ref_dispute_id | dispute.dispute_id | SET NULL | CASCADE |

**Why RESTRICT on the two host/service edges:** a user who still hosts a group, and a
service still sold by a group, must not disappear and orphan money. The delete must be
refused until the group is closed — that is a business decision, expressed as a referential
action.

---

## 3. Attribute count

| Relation | Attributes | Of which keys |
|---|---|---|
| app_user | 8 | 1 PK |
| payment_method | 6 | 1 PK + 1 FK + 1 UQ |
| digital_service | 7 | 1 PK + 1 UQ(composite) |
| carpool_group | 8 | 1 PK + 2 FK |
| credential_vault | 6 | 1 PK/FK + 1 FK |
| membership_seat | 6 | 1 PK + 2 FK + 1 UQ |
| escrow_payment | 7 | 1 PK + 1 FK(UQ) |
| monthly_payout_log | 7 | 1 PK + 1 FK + 1 UQ |
| password_change_log | 5 | 1 PK + 2 FK |
| dispute | 9 | 1 PK + 2 FK |
| credit_event | 7 | 1 PK + 2 FK |

Total: 11 relations, 76 attributes, 15 foreign keys.
