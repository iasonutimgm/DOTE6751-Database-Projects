# SubSplit — Q&A Preparation

Fifteen questions this design invites, ordered by how likely they are. Each answer is
written to be said out loud in under thirty seconds.

---

**1. Why did you store the remaining balance if it is derivable from the ledger?**
"It is read on every page, while the ledger is written once a month. A CHECK constraint
makes the arithmetic a rule of the database, a trigger keeps it true, and query Q11 audits
every row. The audit returns nothing — that is the evidence."

**2. Is the schema really in 3NF?**
"Yes, and stronger: BCNF. The proof workbook lists every functional dependency and every
candidate key, relation by relation. The only non-BCNF-looking thing is the derived balance,
and that is a materialisation decision, not a dependency."

**3. Why manual review instead of automatic refunds?**
"Two coordinated members could drain any host. Detection can be automated — that is what Q05
does — but judgement cannot. The state machine records who decided, when, and why."

**4. Why not a NoSQL database?**
"Because the invariants are multi-row: a seat cannot exceed the product ceiling, a month
cannot be paid twice, the balance must equal the ledger. Those are exactly what a relational
engine enforces and a document store leaves to the application."

**5. How do you prevent one person taking two seats in the same group?**
"UNIQUE (group_id, member_id). It is a key, not a check — the engine refuses the second row."

**6. How do you prevent a group selling more seats than the product allows?**
"A trigger counts the active seats and compares them with digital_service.max_seats. We put
the ceiling in the product because copying it into every group would be a transitive
dependency."

**7. What happens if a host deletes their account?**
"RESTRICT. The group must be closed and the escrow settled first. Deleting a host with live
money would orphan the escrow; that is a business decision expressed as a referential action."

**8. Why is the credential a separate table rather than columns on the group?**
"Because it is a weak entity with its own history. Separating it gives us a 1:1 by
construction and lets us journal every change in password_change_log."

**9. Why is membership_seat a table if it is just a link?**
"It is not just a link — it has a twelve-month window, a state, and it can be complained
about. That is the textbook case for promoting a relationship to an entity."

**10. Where does the 5% fee appear in the schema?**
"platform_fee on each ledger row. The fee is deducted from the release, not charged on top,
so sum(amount − platform_fee) is what the host actually receives."

**11. What stops a month being paid twice?**
"UNIQUE (escrow_id, release_month). Re-running the monthly job is idempotent — the second
insert fails."

**12. How big can this get?**
"The ledger grows one row per seat per month. At a hundred thousand seats that is 1.2 million
rows a year — comfortable for InnoDB, and the natural next step is yearly partitioning."

**13. You said 300 users — is the data real or made up?**
"Seeded, deterministically, from scripts in the repository. Every number on the slides is
computed by a query at presentation time, not typed into the slide."

**14. What would you do differently with another month?**
"Implement the escrow as an actual payment integration, add partial-month proration, and
turn the market listing into a materialised view once the number of open groups grows."

**15. What was the hardest part?**
"Deciding where each constraint belongs. Putting everything in the application is easy and
fragile; putting everything in triggers is clever and unmaintainable. The inventory document
records the line we drew and why."

---

## If you get a question you cannot answer

Say: "We did not model that; the closest thing we have is X." Then show X. Never invent a
table or a number — the schema is on screen and someone will check.
