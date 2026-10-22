# Q&A Preparation

**LinkedIn, reverse-engineered · DOTE 6751 · November 2026**

Fifteen questions we expect, with answers that point at a file the marker can open. Where a
number appears, it is from `query_results/` and can be re-derived by running the query.

---

## A. About the model

**Q1. Why twelve tables? Why not fewer?**
Because the number is what the mapping produces, not a target. Twelve is one relation per
entity set in the Chen diagram — seven strong entities, two associative entities for skills,
and the three tables of the loop (`application`, `interview`, `referral`). Merging, say,
`interview` into `application` would be a repeating group and violate 1NF; merging
`referral` into `application` would add a nullable column and a second candidate key. The
per-table justification is in `design/Relational_Schema.md` §1 and the reduction rules in §2.

**Q2. Why is there no `current_company_id` on `member`?**
Because it is functionally determined by `experience` when `is_current = 1`. Storing it
creates a redundancy the DBMS cannot police: two rows, one fact, silent disagreement after an
edit. Instead a generated column plus a unique index allows unlimited past positions and
exactly one live one. See `design/Normalization_Proof.xlsx`, sheet **Judgement_Calls**, and
`Design_Rationale.md` §4.1.

**Q3. Why is the referral a separate table instead of a column on the application?**
It is 1:1 and optional. A nullable `referral_id` on `application` would add a second candidate
key to the table and would allow a referral row whose application does not exist. As a
separate table it is impossible to represent a referral without its application, and the
candidate and posting are read through the application rather than duplicated. The rejected
alternative is worked through in `Normalization_Proof.xlsx`, sheet **T09 referral**.

**Q4. What is the strongest evidence that the schema is in 3NF?**
Each relation's non-trivial functional dependencies are enumerated and tested one by one:
every determinant is a candidate key, so all twelve relations are in BCNF, which implies 3NF.
Two subtleties are recorded rather than hidden: `job_posting.recruiter_id` does *not* determine
`company_id` (a recruiter can move), and `member.headline` is a snapshot rather than a
projection of `experience`. See `Normalization_Proof.xlsx`, sheets **Summary** and
**Judgement_Calls**.

**Q5. Where is the E-R model's weak entity or generalisation?**
There is none, deliberately. No entity in this domain depends on an owner for its identity —
an application survives the closing of its posting and the deletion of its company — and the
roles (recruiter, referrer, interviewer) are relationship sets over `member`, not subtypes.
Modelling them as subtypes would add a join per role to every query. The decision is recorded
in `Relational_Schema.md` §2, row 6.7.7.

---

## B. About data and implementation

**Q6. Is the data real?**
No. It is synthetic but self-consistent: the generator is deterministic (`random.Random(20261115)`),
and twenty-two cross-table invariants are checked after every rebuild — a hire has at least
three passed interviews, a rejection after interviews ends in a failed round, a terminal
status carries a timestamp, a referral's referrer works at the hiring company, hires never
exceed openings. See `query_results/_consistency_report.json`.

**Q7. If I insert a bad row, what stops me?**
Fourteen specific statements were attempted and all fourteen were refused. Examples: a
duplicate application is rejected by `uk_app_job_member` (1062); an inverted salary band by
`ck_job_salary` (3819); an illegal status jump by `trg_application_status_guard` (1644); a
referral from outside the company by `trg_referral_before_insert` (1644). The transcript is in
`design/Constraint_Inventory.md` §4 and is reproducible with `build/fault_injection.py`.

**Q8. Why are some rules triggers and not CHECK constraints?**
A CHECK sees one row of one table. The state machine compares OLD and NEW, the interview rule
reads the application's status and the maximum round number, and the referral rule reads the
application's channel and the referrer's employment. Those are exactly the four triggers in
`04_views_triggers.sql`. Everything a single row can decide is a CHECK: twenty-five of them.

**Q9. What happens when a member is deleted?**
Their profile parts cascade — education, experience, skills, connections, applications. But a
member who has interviewed someone, referred someone, or posted a job is protected by
`RESTRICT`, because those rows attribute a decision to a person. This asymmetry is deliberate
and listed as a limitation: destroying applications also destroys funnel history, which is
why soft delete is the first item on the improvement list (`Design_Rationale.md` §7, L6).

**Q10. How long does it take to rebuild?**
Three commands, under a minute on this machine: `01_schema.sql`, `02_seed.sql` (about 300 KB
of INSERTs), `04_views_triggers.sql`, then `03_queries.sql` for the results. `build/build_all.py`
runs the whole chain plus the audit. No manual step, no GUI.

---

## C. About the queries and the findings

**Q11. How do you know the referral finding is not an artefact of the generator?**
We do not claim it is an empirical fact about LinkedIn — it is a property of this instance.
What we claim is that the *schema* makes the question answerable: channel is a column on the
application and interviews are their own relation, so the funnel can be decomposed. The
generator draws channels and outcomes independently enough that the ordering is not forced by
construction. The honest statement is in `Requirements.md` A9 and in slide 12's limitation
list.

**Q12. Walk me through Q18.**
Anchor: employees of the hiring company, from `experience` where `is_current = 1`. Recurse:
walk `connection` in both directions, at most two hops, carrying the bridge. Reduce: keep the
minimum hop count per member. Cross: join `member_skill` against the posting's REQUIRED skills
at or above the minimum proficiency, anti-join on existing applications, and exclude the
company's own employees. It returns fifteen candidates for job 79 in the seeded instance.

**Q13. Why cap the recursion at two hops?**
Each hop multiplies the frontier by the average degree (about 7 in this instance), and the
graph is small-world: at two hops most of the network is already reachable. Three hops would
return everyone and stop being a shortlist. At production scale the fix is a materialised
reachability table, not a deeper recursive query — see `Design_Rationale.md` §8.

**Q14. The cycle-time query says 30 days. Is that credible?**
It is credible for this instance and it is decomposable: fifteen to twenty of those days are
the gaps between interview rounds, not the rounds themselves. The caveat is L3 in
`Design_Rationale.md`: stage entry is approximated by the application date because the schema
keeps one decision timestamp rather than a transition log. That makes the total exact and the
per-stage split optimistic.

**Q15. What would you do differently with another three weeks?**
Three things, in order. A status-history table, so per-stage time is measured rather than
inferred. An offer table, so compensation above the band stops being invisible. Soft deletes,
so a departing member does not take the funnel history with them. After those, the graph
query would move to a store that is designed for reachability, and the funnel views would be
materialised for dashboard latency.

---

## D. If the question is hostile

- **"This is just a CRUD schema."** The schema is ordinary on purpose; the contribution is the
  derivation and the evidence. Point at the 22 invariants and the 14 refusals — a CRUD schema
  that cannot be broken is a different artefact from one that has never been tested.
- **"Your data is made up, so your findings are made up."** Agree, then separate the two
  claims: the findings are properties of the instance and are labelled as such; the schema's
  ability to answer the question is not a property of the instance. Slide 12 states both.
- **"Why not use a graph database for connections?"** Because one table answers the two-hop
  question in ten milliseconds at this scale, and a second store would add a consistency
  problem. `Design_Rationale.md` §8 says where that stops being true.
