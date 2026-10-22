# SubSplit — Requirements and Scope

**Course:** DOTE 6751 Database Systems · Group Project · November 2026
**Team:** Xuanmo AN, Yi HOU, Zhao Han HUANG, Jinyu LI, Yitong NI, Shujing YE, Shiyao ZHANG

## 1. The problem

A streaming family plan is priced for a household: six seats for roughly the price of one
and a half individual subscriptions. Most subscribers do not have five people to share it
with, so they turn to social media group buys. That substitute works, but it carries no
institution: the host can change the password at any moment, the member has already paid
for a year, and neither side has a record it can point at.

SubSplit is the missing institution. It does not resell subscriptions itself; it holds the
member's prepayment in escrow, releases one twelfth per month to the host, and keeps a
verifiable record of both parties' conduct.

## 2. Actors

| Actor | Description | Main goals |
|---|---|---|
| **Member** (guest) | Pays for a seat in someone else's group | Pay once, keep access, get money back if the host misbehaves |
| **Host** (owner) | Owns the subscription account and sells seats | Collect monthly income without chasing six people for transfers |
| **Admin** | Platform staff | Review complaints, release or refuse refunds, suspend abusive hosts |

A single user account may act as host and member at the same time; the platform does not
separate the two roles, it only distinguishes ordinary users from administrators.

## 3. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | A user registers with a display name, one or more payment instruments, and a credit score starting at 100. |
| FR-2 | A host creates a group for one digital service (brand + region + plan) and sets the monthly price per seat. |
| FR-3 | The platform records the household credential (invite link, encrypted passphrase) for each group and tracks when it last changed. |
| FR-4 | A member joins a group by taking a seat; the seat carries its own twelve-month window. |
| FR-5 | The system refuses a seat beyond the service's official seat ceiling, and refuses seats in frozen or closed groups. |
| FR-6 | Joining creates an escrow record for the full twelve months of prepayment. |
| FR-7 | Each month the platform releases one twelfth of the prepayment to the host and keeps a 5% fee; the release is written to a ledger. |
| FR-8 | A month cannot be released twice for the same escrow. |
| FR-9 | Any credential change is journalled with a timestamp and the person who made it. |
| FR-10 | A member may file a dispute against a seat; the dispute moves through OPEN → UNDER_REVIEW → REFUNDED / REJECTED, and only an administrator may leave the review states. |
| FR-11 | While a group is under a live dispute, its remaining escrow balance is frozen. |
| FR-12 | A refund, a late release, or a successful complaint changes the responsible user's credit score, and the change is journalled with the resulting score. |
| FR-13 | Members can search the open market by service, region, seats left and host reputation. |
| FR-14 | Administrators can see the platform's monthly revenue, its fastest-filling services, and the groups whose behaviour suggests fraud. |

## 4. Non-functional requirements

- **Integrity first.** Money must never be silently lost or duplicated: the stored escrow
  balance must equal the sum of its ledger at all times.
- **Auditability.** Every state that costs someone money (credential change, dispute
  decision, credit movement) leaves a row that cannot be edited away.
- **Portability.** Plain MySQL 8.0, no extensions; the schema must load in Navicat and in
  the command-line client with identical results.
- **Read performance.** The two hottest reads — "groups with one seat left" and "my
  escrow balance" — must not require scanning the ledger.

## 5. Scope

**In scope:** the data model and its analytical queries; escrow bookkeeping; dispute state
machine; reputation record; a seeded, self-consistent data set.

**Out of scope:** real payment-gateway integration, credential encryption implementation,
notification delivery, the streaming providers' own terms enforcement. These are modelled
as states and records only.

## 6. Assumptions

| ID | Assumption |
|---|---|
| A1 | One seat = one member = one twelve-month prepayment. No partial months. |
| A2 | The monthly release is exactly 1/12 of the prepayment; the 5% fee is deducted from that release, not charged on top. |
| A3 | A refund returns the unreleased remainder; months already released are not clawed back. |
| A4 | A group's seat ceiling is a property of the service, not of the individual group. |
| A5 | A user may hold at most one seat per group (enforced by a unique constraint). |
| A6 | Credit score is bounded to 0–100; a score below 30 suspends the account. |
| A7 | Hosts are responsible for the account; the platform never stores the plaintext password. |
| A8 | Presentation date is November 2026; the seeded data is anchored to October 2026. |
