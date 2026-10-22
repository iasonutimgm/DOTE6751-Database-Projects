# SubSplit — Product Specification

**Version** 1.0 · **November 2026** · **DOTE 6751 Database Systems · Group Project**

---

## 1. One line

SubSplit is a subscription-sharing platform with escrow: it opens the six-seat family
discount to people who are not a family.

## 2. Vision

Anyone should be able to buy a service at the household price, without that discount
depending on the other person's good character.

Three beliefs sit under it:

1. **The discount is real; the trust is missing.** A family plan prices a seat at roughly
   one sixth of the individual rate. That gap is not going away.
2. **The household cannot solve it.** Nobody has five friends who happen to want the same
   service for the same twelve months, and a verbal promise between strangers has no force.
3. **The missing piece is an institution, not a better chat app.** Specifically: custody of
   the money, plus a verifiable record of what each side did.

## 3. The problem and the existing substitutes

**Problem.** Family plans are priced for six. Most subscribers are one. So people assemble
group buys on social media.

**Why the substitutes fail:**

| Substitute | Apparent benefit | Where it breaks |
|---|---|---|
| Group buy in a chat group | Free, fast | The host changes the password or disappears; a year of prepayment has no route back. The host, in turn, spends the first week of every month chasing five small transfers. |
| Reseller / top-up shop | A platform in the middle | It is account trading, against the provider's terms, and can be shut down at any time. There is no notion of a seat. |
| Sharing with family | Zero trust cost | Tiny reach — and it stops working the moment there are not six of you. |
| Buying individually | Simplest | Costs more than twice as much. |

**The common gap:** money is paid once, service is delivered monthly, and nothing in between
guarantees that the person who paid keeps access. SubSplit occupies exactly that gap.

## 4. Users and scenarios

| Role | Who | What they fear | What the platform gives them |
|---|---|---|---|
| **Member** | A student living alone, a young professional | Paying for a year and being removed in month two | Money in escrow, released monthly; a complaint freezes the balance |
| **Host** | Someone who already owns a family plan | Chasing five people for a transfer every month | An automatic monthly payout |
| **Admin** | Platform operations | Not knowing who is lying | Credential history, complaint clusters, credit history — then a decision |

**Three scenarios**

- **A — finding a seat.** A Spotify HK group is one seat short, host score 100. The member
  searches *Spotify · HK · one seat left · score 100* and sees two candidates in under a
  second; takes the cheaper one.
- **B — opening a group.** A host verifies the official invoice, opens a group at HK$18 per
  seat per month, fills six seats, and receives HK$17.10 per seat every month after the 5% fee.
- **C — a dispute.** A host changes the password six times in two months and two members
  cannot get in. The group enters the risk queue, the remaining balance is frozen, and an
  administrator decides whether to refund.

## 5. How it runs

**Four steps**

1. **The host verifies the bill.** The official invoice is checked before the group goes live.
2. **The group opens six seats.** The host sets the monthly price per seat.
3. **Members prepay twelve months.** The money does not reach the host; it enters escrow.
4. **The platform releases one twelfth a month.** The host is paid monthly, the platform
   keeps 5%, and the escrow is empty at month twelve.

**Where the money currently sits** (seeded instance):

| Item | Amount (HK$) |
|---|---|
| Prepaid by members | 61,577 |
| Released to hosts | 35,464 (58%) |
| Still held in escrow | 26,113 |
| Platform fees collected | 1,772 |

**How a dispute resolves**

Complaint → the remaining escrow for that seat is frozen → an administrator reviews → refund
(the unreleased balance goes back) or rejection → the credit score changes, with a row that
records why. Months already released are never clawed back.

## 6. Feature set

| Stage | Features | Status |
|---|---|---|
| **MVP** | Registration and credit score, payment instruments, group creation and pricing, credential vault, seats with a twelve-month window, escrow prepayment, monthly release, credential journal, complaints with manual review, credit audit trail | Implemented at the data layer |
| **Phase 2** | Automated bill verification (API), notifications, ratings, cross-region pricing, mobile client | Not built |
| **Explicitly out** | Reselling subscriptions, a real payment gateway, storing plaintext passwords, automatic refunds | Not built, for stated reasons (see §10) |

**Scope note.** What exists is the *data layer*: tables, constraints, triggers, queries. The
payment gateway, notifications and the interface are phase 2 and are modelled as states and
records, not as real money movement.

## 7. Business model and unit economics

**Revenue:** 5% of every release.
**Cost:** hosting and database, payment processing, support (the manual review), bad debt.

**Rough arithmetic** (on the seeded instance): 300 seats at roughly HK$20 per seat per month
is about HK$70,000 of releases a year, and therefore about HK$3,500 of revenue. At this scale
it is a proof of concept, not a business.

**Break-even has two directions only:** more seats (scale), or a higher take rate (which
raises the per-seat price and weakens the value proposition). Five per cent is deliberately
conservative — under twice a payment processor's fee, and small enough that nobody feels
taxed.

## 8. Metrics (all computable from the current tables)

| Metric | Definition | Source |
|---|---|---|
| Time to fill | Hours from group creation to the last seat | `carpool_group.created_at` / `full_at` |
| MRR | Fees released in the month | `monthly_payout_log` |
| Dispute rate | Seats with at least one complaint / all seats | `dispute` / `membership_seat` |
| Refund rate | Complaints closed as refunded / all seats | `dispute.dispute_status` |
| Risk hits | Groups with ≥3 credential changes and ≥2 complaints in 30 days | `password_change_log` + `dispute` |
| Host retention | Hosts with a release in each of six consecutive months | `monthly_payout_log` |
| Credit distribution | Users per score band | `app_user.credit_score` |

## 9. Competition

| Alternative | Its advantage | Our difference |
|---|---|---|
| Chat-group group buy | Free, immediate | Escrow, a record, an arbiter |
| Top-up resellers | A platform guarantee | Compliant (no account trading), priced per seat |
| Official family plan | Safest | Requires an actual family |
| Individual subscription | Nothing to coordinate | More than twice the price |

**The moat is not the technology, it is the record.** A person's history on the platform
cannot be carried elsewhere. That is why the credit score must be derived from the ledger and
must never be editable by hand.

## 10. Risks, compliance, and what we do about them

| Risk | Impact | Response |
|---|---|---|
| Violating a provider's terms | Accounts closed, members lose access | Position as a cost-sharing tool, not account trading; refundable balance; no account sales |
| Host absconds with the money | Member loses a year | Money never reaches the host; monthly release; a complaint freezes the balance |
| Malicious complaints | A host is punished unfairly | Manual review; a complaint must name a seat; credit moves only on a decision |
| The platform itself fails | All balances lost | Client funds segregated from operating funds (a phase-2 requirement) |
| Privacy | Credential leak | Encrypted string only, never plaintext, rotatable at any time |

## 11. Roadmap

| Stage | Goal | Key work |
|---|---|---|
| Now | A model that runs, data that reconciles | 11 tables, 12 acceptance checks, 18 queries |
| Next | Real bill verification | Provider API instead of manual upload |
| Then | Payments and compliance | Real escrow account, split settlement, refunds |
| Later | Growth | Referrals, cross-service groups, a business tier |

## 12. Appendix — feature ↔ table ↔ query

| Feature | Lives in | Verified by |
|---|---|---|
| Group creation and pricing | `carpool_group` + `digital_service` | Q01 precise seat hunting, Q07 price comparison |
| Seats and the twelve-month window | `membership_seat` | Q06 one member's seats |
| Prepayment and balance | `escrow_payment` | Q11 balance audit |
| Monthly release and fee | `monthly_payout_log` | Q04 MRR, Q17 month-over-month |
| Credential history | `password_change_log` | Q05 risk control |
| Complaints and review | `dispute` | Q16 complaint mix, Q09 refund rate |
| Credit score | `credit_event` | Q14 low-credit hosts |
| Payment instruments | `payment_method` | constraint C08 (one default) |
| Seat ceiling | trigger + `digital_service.max_seats` | fault injection #1 |

**In one sentence:** every feature in this document points at a specific table, and every
number in it can be recomputed by a query.
