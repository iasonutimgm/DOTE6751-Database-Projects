# SubSplit — Presentation Script

**Total slot:** 10 minutes · **Target:** 8 minutes speaking + 2 minutes Q&A
**Presenters:** two (A and B). Rotate twice, not six times.
**Deck:** 14 slides, but slides 13–14 are appendix and are never presented.

Legend: **[A]** = first presenter, **[B]** = second presenter, *(pause)* = stop talking for a second.

---

## 0:00 – 0:40  Slide 1 — Title
**[A]** "Every one of us has been in a group chat where somebody is collecting money for a Netflix family plan. This is a project about that chat, and about why it keeps breaking."

*(Do not read the member names. Click.)*

## 0:40 – 1:40  Slide 2 — Motivation
**[A]** "A family plan is priced for six people. The discount is real — roughly one and a half individual subscriptions for six seats. But the six people are strangers.

The member has paid for a year and holds nothing. The host owns the account and can change the password at any time. Meanwhile the host spends the first week of every month chasing five small transfers.

So the design question is not how to split a bill. It is how to make a stranger's promise enforceable."

*(Pause on the last sentence. Click.)*

## 1:40 – 2:40  Slide 3 — How it works
**[A]** "Four steps. The host verifies the bill and opens a group. Members prepay twelve months — but the money does not go to the host, it goes into escrow. Every month the platform releases one twelfth and keeps five per cent.

The numbers on the right are live from our database: sixty-one thousand dollars prepaid, thirty-five thousand already released, twenty-six thousand still held. That is the money the platform is protecting right now."

## 2:40 – 4:20  Slides 4–6 — The model
**[B]** "Eleven relations, fifteen foreign keys. I will not read them out loud — three things matter.

First, the credential vault is a weak entity. It borrows the group's key, so a group cannot have two credentials and a credential cannot exist without a group.

Second, the seat is not a simple link table. It has a life cycle — joined, expiring, leaving, refunded — so we promoted the M:N relationship to an entity.

Third, the ledger is keyed on escrow plus month. A month cannot be paid twice, and that is a constraint, not a convention.

*(Slide 6)* Money has three homes: what was prepaid, what has been released, what is still owed. The CHECK constraint is why a careless UPDATE cannot invent money."

## 4:20 – 6:10  Slides 8–11 — The queries
**[B]** "Eighteen queries, six on stage. I will show two.

*(Slide 8)* This is the one a member runs: recruiting groups on Spotify Hong Kong with exactly one seat left and a host with a perfect score. Two rows — and both are real.

*(Slide 9)* This is the one an administrator runs. A host who changed the password six times in thirty days, and two members who could not log in. Neither condition alone is proof. Together they describe a pattern. The query returns five groups; it does not punish anyone. The decision stays human, and the state machine makes that decision visible."

## 6:10 – 7:20  Slides 10–11 — What the data says
**[A]** "Revenue is modest and honest: about HK$176 in the peak month. What is more interesting is what people buy. Netflix Hong Kong leads, then ChatGPT, then YouTube — and the order tracks the size of the discount, not the popularity of the brand.

*(Slide 11)* Two questions need a window function: consecutive blocked months, and month-over-month fee growth. Same tool, two different questions."

## 7:20 – 8:00  Slide 12 — Limits
**[B]** "Three things we did not do. We modelled escrow as a state machine rather than a payment gateway. We do not model partial months. And a determined host can still lie — we can only make the lie visible.

Every one of those is a decision with a next step, which is why the design is finished rather than unfinished."

*(Stop. Do not summarise. Ask for questions.)*

---

## Q&A handling

- **Answer in one sentence, then stop.** Elaboration is what runs over time.
- If a question is about a number, open Navicat and show it — that is faster than arguing.
- If a question is about something we did not build, say so and point at the "Limits" slide.

## Timing checkpoints

| At | Should be on |
|---|---|
| 2:00 | slide 3 |
| 4:20 | slide 6 |
| 6:10 | slide 9 |
| 7:20 | slide 11 |
| 8:00 | done |

If you are behind at 4:20, skip slide 6 and go straight to the queries. Queries are worth more than the model slide.
