# LinkedIn Hiring Loop — Product Specification

(reverse-engineered)

**Version** 1.0 · **November 2026** · **DOTE 6751 Database Systems · Group Project**

---

## 1. One line

A reverse-engineered data model of LinkedIn's hiring loop: it turns "how a hire actually
happens" from a black box into a process you can trace row by row.

## 2. Vision

The most valuable part of recruiting data is never shown to the people who use the product.
They see "hired"; they do not see the 250 applications, 210 interviews and twelve legal
status transitions behind it.

The claim we want to test is simple: **record those intermediate states properly, and hiring
stops being a feeling and becomes a set of numbers that can be measured, compared and
improved.**

## 3. The problem and the substitutes

Recruiting products give you outcomes, not process. So three common claims can only be
asserted, never tested:

| What people say | What would be needed to test it |
|---|---|
| "Referrals produce better candidates" | A channel column on the application, and interviews as their own relation |
| "We are slow because interviews do not get scheduled" | A stage-entry time, not a single decision timestamp |
| "The market lacks skill X" | Requirements and holdings that can be joined |

**Why the substitutes fall short:**

| Substitute | Apparent benefit | Where it breaks |
|---|---|---|
| Built-in recruiting dashboards | Available immediately | Outcome metrics only — no channel, round or interviewer dimension |
| Spreadsheets by hand | Flexible | One file per person; cross-table questions do not survive an edit |
| An ATS | Purpose-built | A closed model: a question it did not anticipate needs a vendor ticket |
| Qualitative interviews | Insightful | Not reproducible, not comparable |

**The common gap:** nobody models *application → interview → referral → hire* as a set of
relations. That is precisely what the reverse-engineering does.

## 4. Users and scenarios

| Role | Who | The question they want answered | What they get |
|---|---|---|---|
| **Candidate** | A job seeker | How far am I from this role? | A missing-skill list (Q09) |
| **Recruiter** | HR or hiring manager | Which channel actually works? | Funnel by channel (Q07) |
| **Referrer** | A current employee | Did my referral land? Is the bonus paid? | Referral state and leaderboard (Q08) |
| **Analyst** | Anyone studying hiring | Is the bottleneck the process or the people? | Cycle breakdown and interviewer pass rates (Q10, Q11) |

**Three scenarios**

- **A — closing a gap.** A candidate sees 28 half-matching roles; five of the twelve closest
  are missing *statistical analysis*. That is one course, not another hundred applications.
- **B — comparing channels.** Referral and direct differ by two points on interview rate
  (46.7% vs 44.7%) but by three times on hire rate (16.7% vs 5.3%). The leverage is after the
  interview, not in sourcing volume.
- **C — finding a warm path.** The target role is at IBM and the candidate has no first-degree
  contact — but 33 people are reachable within two hops, 15 of whom pass the skill filter.

## 5. How it runs

**Six steps, and the row each one writes**

| Step | Writes |
|---|---|
| Company posts | `job_posting` + `job_skill` (skills, seniority, band, openings) |
| Member applies | `application` (channel: direct / referral / sourcing) |
| Recruiter screens | `application.status = SCREENING`, or REJECTED / WITHDRAWN |
| Interviews run | `interview` (round 1..n, interviewer, outcome, score) |
| Offer and decision | `status → OFFER → HIRED / REJECTED`, `decided_at` stamped |
| Referral settles | `referral.bonus_status`: PENDING → PAID / FORFEITED |

**The seeded instance:** 300 members, 60 companies, 120 postings, 250 applications, 210
interviews, 60 referrals, 21 hires.

## 6. Feature set

| Stage | Features | Status |
|---|---|---|
| **MVP** | Members and profiles, companies and postings, skill vocabulary and matching, application state machine (12 legal transitions), interview rounds and scores, referrals and bonus state, undirected social graph stored once | Implemented at the data layer |
| **Phase 2** | Messaging and notifications, résumé parsing, job recommendations, salary prediction, multi-currency | Not built |
| **Explicitly out** | Scraping LinkedIn, account login, full-text résumé search | Not built (see §10) |

**Scope note.** This is *reverse engineering*: a logical structure inferred from publicly
visible product behaviour, not an internal schema. Every table and column name is ours.

## 7. Business model and unit economics (of the modelled product)

Recruiting platforms earn from job postings, enterprise subscriptions and agency services.
The model covers the data those depend on.

**Referral bonuses are a real cost, and this model can price them:**

| Item | Amount |
|---|---|
| Bonuses paid | $26,500 |
| Bonuses pending | $38,000 |
| Referrals on file | 60 |
| Hires whose bonus is still pending | 2 |

**The point:** "always pay a referral bonus" and "pay on outcome" are two different cost
structures, and one enum value in the schema expresses the difference.

## 8. Metrics (all computable today)

| Metric | Definition | Source |
|---|---|---|
| Interview rate | Applications reaching interview / all applications | `application.status` |
| Hire rate | Hires / all applications | `application.status = HIRED` |
| Channel gap | Referral hire rate − direct hire rate | `application.source_channel` |
| Time to hire | Average days from application to decision | `applied_at` → `decided_at` |
| Stage time | Before first interview / between interviews / before decision | `interview.scheduled_at` |
| Interviewer pass rate | PASS outcomes / interviews run | `interview.outcome` |
| Skill gap | Posting REQUIRED skills − member holdings | `job_skill` vs `member_skill` |
| Bonus cost | Paid + pending | `referral.bonus_status` |

## 9. Competition

| Substitute | Its advantage | Our difference |
|---|---|---|
| Built-in dashboards | Free, immediate | We can ask cross questions: channel × round × interviewer |
| An ATS | Complete workflow | Our model is open — one SQL statement changes the definition |
| Spreadsheets | Flexible | Self-consistent, reproducible, with 22 checks behind it |
| Qualitative research | Insight | We produce comparable numbers |

## 10. Risks, compliance and limits

| Risk | Impact | Response |
|---|---|---|
| The data is synthetic | Conclusions do not describe the real market | Every finding is labelled as "on the seeded instance" |
| Reverse engineering ≠ the real schema | Differs from LinkedIn's implementation | Stated plainly: inferred from public behaviour, with assumptions |
| Single currency | Cross-country comparison is nominal | Annual USD throughout; no FX conversion |
| Stage time approximated by the application date | Per-stage durations are imprecise | Documented as the first improvement item (add a status history table) |
| Two-hop ceiling | Three hops need a graph store | Stated boundary, no approximation |

## 11. Roadmap

| Stage | Goal | Key work |
|---|---|---|
| Now | A model that runs; 22 consistency checks green | 12 tables, 4 views, 4 triggers, 18 queries |
| Next | Stage log | Add `application_status_history`, retire the single `decided_at` |
| Then | Offer table | Base, bonus, currency and acceptance date |
| Later | Soft delete | `member.deleted_at` + RESTRICT, preserving funnel history |

## 12. Appendix — feature ↔ table ↔ query

| Feature | Lives in | Verified by |
|---|---|---|
| Postings and skill requirements | `job_posting` + `job_skill` | Q09 skill gap |
| Applications and channel | `application` | Q07 funnel by channel |
| Interview rounds | `interview` | Q10 stage time, Q11 interviewer pass rate |
| Referrals and bonuses | `referral` | Q08 referrer leaderboard |
| Social graph | `connection` | Q18 two-hop introductions |
| Skill matching | `member_skill` + `job_skill` | Q09 match percentage |
| Current employer | `experience.is_current` + unique index on a generated column | constraint C12 |

**In one sentence:** every feature in this document points at a specific table, and every
number in it can be recomputed by a query.
