# Presentation Script

**LinkedIn, reverse-engineered · DOTE 6751 · November 2026**
Target length 13 minutes, 14 slides. The speaker notes inside `LinkedIn.pptx` carry the
same content; this file adds timing, transitions and delivery cues.

| Slide | Section | Start | End | Speaker |
|---|---|---|---|---|
| 1 | Title | 0:00 | 0:40 | Xuanmo AN |
| 2 | Motivation | 0:40 | 1:50 | Xuanmo AN |
| 3 | The hiring loop | 1:50 | 3:20 | Xuanmo AN |
| 4 | ERD panorama | 3:20 | 4:30 | Jinyu LI |
| 5 | Module A — identity | 4:30 | 5:30 | Jinyu LI |
| 6 | Modules B and C | 5:30 | 6:30 | Jinyu LI |
| 7 | The twelve tables | 6:30 | 7:20 | Zhao Han HUANG |
| 8 | Evidence I — channels | 7:20 | 8:30 | Yitong NI |
| 9 | Evidence II — skill gap | 8:30 | 9:50 | Yitong NI |
| 10 | Evidence III — warm intro | 9:50 | 11:10 | Yitong NI |
| 11 | Evidence IV — cycle time | 11:10 | 12:10 | Shujing YE |
| 12 | Improvements and limits | 12:10 | 12:50 | Yi HOU |
| 13 | Task allocation | 12:50 | 13:10 | Shiyao ZHANG |
| 14 | Q&A backup | 13:10 | — | all |

---

## Slide 1 · Title — 0:00–0:40

> Good morning. We reverse-engineered the part of LinkedIn that turns a job posting into a
> hire. There was no schema to read, so we derived one from behaviour, implemented it in
> MySQL 8.0, populated it with a self-consistent instance, and wrote eighteen queries that
> the product answers but never shows. Twelve tables, one closed loop.

**Cue.** Do not read the title. Point at the Chen diagram on the right and say "this is the
model; the rest of the deck is the evidence for it". Pause briefly before advancing.

---

## Slide 2 · Motivation — 0:40–1:50

> Three observations set the scope. First, the product shows outcomes, not process: a filled
> role is a badge, but the 250 applications and 210 interviews behind it are invisible — and
> they are the interesting data. Second, referrals are the channel every recruiter praises
> and almost nobody measures; here they can be measured. Third, skill shortages are usually
> asserted in strategy documents, and with postings and profiles in one schema they become
> computable.

**Cue.** Land on the right-hand numbers: 250 applications, 8.4 % end-to-end hire rate, 3.1×
referral advantage. Say explicitly that those are computed from the seeded instance and
that every one of them can be reproduced with `03_queries.sql`.

**Transition.** "To see why those numbers exist, you need the process."

---

## Slide 3 · The hiring loop — 1:50–3:20

> Six steps. A company posts, a member applies through one of three channels, a recruiter
> screens, interviews run in rounds, an offer is made and decided, and a referral settles.
> Each step writes a specific row, which is the point: the diagram is a data-flow diagram as
> much as a process diagram.

> On the right is the state machine. Seven states, twelve legal transitions, one trigger that
> enforces them. An application cannot jump from submitted to hired, an interview cannot
> precede the application, a terminal status always carries a decision timestamp.

**Cue.** Walk the numbers down the left column with the pointer, then cross to the card and
read the five refusals. If time is short, skip step 6 — it is covered on slide 8.

**Transition.** "That process determines the tables."

---

## Slide 4 · ERD panorama — 3:20–4:30

> Twelve relations, seventeen foreign keys, twenty-five check constraints. Two things to
> notice. The member table is deliberately thin: there is no current-employer column, because
> that fact is already implied by the experience table with a single live row. And the
> application table is the hinge: people on the left, decisions on the bottom, every query
> joins through it.

**Cue.** Trace one path with the pointer: member → application → interview. Do not attempt to
read the attribute lists; they are unreadable at this size by design. Say "full resolution is
in `erd/`".

**Transition.** "Module A first, because everything else references the person."

---

## Slide 5 · Module A — 4:30–5:30

> Identity is four tables around the member. The design decision worth defending is the
> missing current-employer column. Storing it would duplicate a fact that experience already
> carries, and the two copies could disagree after an edit. Instead `is_current` marks the
> live row, and a unique index over a generated column makes a second live row impossible —
> which is how MySQL 8.0 expresses a partial index.

**Cue.** Point at `current_member_id` in the experience table and at the `UQ*` flag. Mention
that this is the one place where the implementation detail matters to the model.

---

## Slide 6 · Modules B and C — 5:30–6:30

> Demand on the left: a company advertises postings, and each posting declares skills with an
> importance flag. Note that importance lives on the pair, not on the skill — the same skill
> is a hard requirement in one posting and a preference in another. That single attribute is
> what makes a match score defensible.

> On the right, the loop. Interviews are numbered per application, and the referral is
> one-to-one with the application, so its candidate and its posting cannot contradict it.

**Cue.** This slide is the bridge to the tables; keep it to sixty seconds.

---

## Slide 7 · The twelve tables — 6:30–7:20

> Twelve tables in three groups, with the row counts of the seeded instance. The counts
> matter: they are the evidence that the model is populated at a scale where the queries
> return distributions rather than anecdotes.

**Cue.** Read only the three group headers and one table per group. The audience can read the
rest; do not narrate a list of twelve.

**Transition.** "Now the queries, in the order that builds an argument."

---

## Slide 8 · Evidence I — 7:20–8:30

> Where do hires come from? Referral applications are the smallest group, sixty of 250, but
> they produce almost half the hires: 16.7 % end to end against 5.3 % for direct. The
> interesting detail is that interview rates are almost identical — 46.7 against 44.7 — so
> the difference sits after the interview, not in sourcing volume. A single "hired" flag
> could never show that.

> On the right, the referral programme by referrer: who refers, who converts, and what the
> bonuses cost. Fourteen thousand dollars paid, seven thousand pending.

**Cue.** Pause after "after the interview" — that is the finding.

---

## Slide 9 · Evidence II — skill gap — 8:30–9:50

> First focus query. For one named candidate, which open roles do they half-qualify for, and
> what exactly is missing? Priya Walker, a project manager at Siemens: twenty-eight open
> postings where she holds at least half the hard requirements. The query returns the match
> percentage and, more usefully, the names of the missing skills, because "sixty-seven per
> cent" is not actionable and "you are missing statistical analysis" is.

> Across the twelve closest matches, statistical analysis is missing five times. That is the
> sentence a career product would want to say.

**Cue.** Emphasise the threshold in the join: matching on skill id alone would overstate fit,
because a skill at proficiency 2 is not the minimum 4 the posting asks for.

---

## Slide 10 · Evidence III — warm introductions — 9:50–11:10

> Second focus query, and the one we are proudest of. Who could introduce me to this hiring
> team? The query walks the connection graph recursively, two hops from the employees of the
> hiring company, and intersects that reachable set with the posting's hard requirements. On
> the IBM delivery manager role: thirty-three reachable people, fifteen survive the skill
> filter, and one is a single hop from an employee.

> It is a recursive CTE plus an anti-join, and it only works because an edge is stored once
> in canonical order. Store both directions and the recursion visits every node twice.

**Cue.** If asked "why two hops", answer immediately: each additional hop multiplies the
frontier; at three hops the query returns the whole network and stops being a shortlist.

---

## Slide 11 · Evidence IV — cycle time — 11:10–12:10

> Where the thirty days go. Across seniority levels a hire takes twenty-nine to thirty-eight
> days; interviews themselves account for fifteen to twenty, so the binding constraint is
> scheduling latency, not deliberation. On the right, interviewer calibration: pass rates
> from zero to a hundred per cent on four to six interviews each. That is a signal about the
> interviewers as much as about the candidates.

**Cue.** Acknowledge the approximation: stage entry is inferred from the application date
because the schema keeps one decision timestamp. This is the honest limitation, and it is
also the first improvement on the next slide.

---

## Slide 12 · Improvements and limitations — 12:10–12:50

> Three structural improvements: a status-history table so stage durations stop being an
> approximation; an offer table, because an above-band offer is currently invisible; and soft
> deletes, because deleting a member today destroys their applications. If we fixed one
> thing, it would be the third — that is a compliance problem before it is a modelling one.

**Cue.** Do not read all five limitations; name the synthetic data and the two-hop ceiling,
and say the rest are in the rationale.

---

## Slide 13 · Task allocation — 12:50–13:10

> Seven members, four dependency layers, eighty-one person-hours. The split follows
> dependencies rather than page count: the schema had to exist before the seed, the seed
> before the queries, and the queries before the deck.

**Cue.** Ten seconds per row at most. This slide exists for the marker, not the audience.

---

## Slide 14 · Q&A — 13:10

> The Chen diagram is on the left if the questions go to the model, and the five questions we
> expect are on the right. The design documents carry the long answers.

**Cue.** Stop talking. Move to the side of the screen so the diagram is visible. If a
question is about a number, open the corresponding CSV rather than paraphrasing it.
