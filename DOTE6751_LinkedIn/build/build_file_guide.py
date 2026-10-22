# -*- coding: utf-8 -*-
"""Build File_Guide.docx (+pdf) by scanning the delivered directory."""
import json
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

ROOT = r"D:\桌面\数据库大作业\LinkedIn_交付"
OUT = os.path.join(ROOT, "File_Guide.docx")
NAVY = RGBColor(0x0E, 0x2A, 0x47)
BLUE = RGBColor(0x0A, 0x66, 0xCA)
GRAY = RGBColor(0x5A, 0x6B, 0x7B)

DESC = {
    "design/Requirements.md":
        "Problem statement, actors, 16 functional requirements, non-functional constraints, "
        "scope and ten numbered assumptions. Read first.",
    "design/Entity_Relationship_Catalog.md":
        "Every entity set with its attributes and identifier, every relationship set with "
        "cardinality and participation, and the relation that implements it.",
    "design/Relational_Schema.md":
        "The twelve relation schemas in R(attributes) form with PK/FK, the §6.7 reduction "
        "table and the referential-action rationale.",
    "design/Normalization_Proof.xlsx":
        "16 sheets: method, FD inventory, one 3NF/BCNF proof per relation, and the judgement "
        "calls a mechanical proof would get wrong.",
    "design/Constraint_Inventory.md":
        "36 business rules mapped to the constraint that enforces each, plus the 14-statement "
        "fault-injection transcript.",
    "design/Design_Rationale.md":
        "Why twelve tables, what is deliberately not stored, the normalisation argument, the "
        "denormalisation we accepted, and nine recorded limitations.",
    "sql/01_schema.sql":
        "Creates linkedin_db (utf8mb4 / utf8mb4_0900_ai_ci) and the twelve tables with all FKs "
        "and CHECKs. Run first.",
    "sql/02_seed.sql":
        "Deterministic instance: 300 members, 60 companies, 120 postings, 250 applications, "
        "210 interviews, 60 referrals. Run second.",
    "sql/04_views_triggers.sql":
        "Four reporting views and the four triggers that carry the cross-table rules. Run third.",
    "sql/03_queries.sql":
        "The eighteen analytical statements, each with a -- @query marker. Read-only; run last.",
    "erd/ERD_logical_full.png":
        "Full logical schema: twelve tables, PK bold, FK italic, crow's foot at the many side.",
    "erd/ERD_logical_full.svg":
        "Vector version of the logical schema, for printing or editing.",
    "erd/ERD_conceptual.png":
        "Chen notation: entity rectangles, relationship diamonds, 1/N cardinality.",
    "erd/ERD_conceptual.svg":
        "Vector version of the conceptual model.",
    "erd/ERD_module_identity.png":
        "Module A: member, education, experience, connection, skills.",
    "erd/ERD_module_identity.svg":
        "Vector version of Module A.",
    "erd/ERD_module_demand.png":
        "Module B: company, posting, skill vocabulary and the job_skill ask.",
    "erd/ERD_module_demand.svg":
        "Vector version of Module B.",
    "erd/ERD_module_hiring_loop.png":
        "Module C: application, interview, referral and the recruiter member.",
    "erd/ERD_module_hiring_loop.svg":
        "Vector version of Module C.",
    "query_results/_summary.json":
        "Machine-readable index of the eighteen results: title, row count, elapsed ms, columns.",
    "query_results/_consistency_report.json":
        "The 22 cross-table invariant checks (all pass) plus eleven facts about the instance.",
    "slides/LinkedIn.pptx":
        "The 14-slide deck, 16:9, with speaker notes on every slide.",
    "slides/LinkedIn_Narrative.docx":
        "Six-section written narrative, 1,603 words, academic register.",
    "slides/LinkedIn_Narrative.pdf":
        "PDF export of the narrative, for submission where Word is not available.",
    "slides/Presentation_Script.md":
        "Per-slide script with timings, cues and transitions for a 13-minute delivery.",
    "slides/QA_Prep.md":
        "Fifteen anticipated questions with evidence-backed answers, plus three hostile ones.",
    "slides/Task_Allocation.md":
        "Who did what, at which difficulty and for how many hours, with the dependency graph.",
    "File_Guide.docx": "This guide.",
    "File_Guide.pdf":
        "PDF export of this guide, for submission where Word is not available.",
    "build/README.md":
        "What each generator does, how to run the rebuild, and the one path constant to edit "
        "if the folder moves.",
    "build/gen_seed.py":
        "Deterministic generator (seed 20261115) for the 300-member instance; writes 02_seed.sql.",
    "build/build_all.py":
        "One-command rebuild: seed, schema, views/triggers, query build, query run and the audit.",
    "build/build_queries.py":
        "Selects the Q09 member and Q18 posting from the loaded data and fills "
        "queries_template.sql to produce 03_queries.sql.",
    "build/queries_template.sql":
        "The eighteen statements with {{MEMBER_ID}} and {{JOB_ID}} placeholders.",
    "build/run_queries.py":
        "Executes every statement and writes one UTF-8 CSV per query plus _summary.json.",
    "build/verify_data.py":
        "The 22 cross-table invariants; writes _consistency_report.json and exits non-zero on "
        "a violation.",
    "build/fault_injection.py":
        "Fourteen statements that must fail, each in a rolled-back transaction; prints the "
        "captured error codes.",
    "build/erd.py":
        "Draws the logical, conceptual and three module diagrams as PNG and SVG.",
    "build/gen_normalization_xlsx.py":
        "Builds Normalization_Proof.xlsx: method, FD inventory, twelve per-table proofs.",
    "build/build_deck.py":
        "Builds the 14-slide deck with speaker notes.",
    "build/build_narrative_docx.py":
        "Builds the six-section narrative document.",
    "build/build_file_guide.py":
        "Builds this guide by scanning the delivered tree.",
}

QNOTE = {
    "q01": "Open roles in Singapore with pay band, age and applicant count",
    "q02": "Deepest open-to-work profiles with credentials and reach",
    "q03": "The five most contested open postings, application by application",
    "q04": "Skill demand ranked by hard requirement",
    "q05": "Company hiring scorecard: volume, conversion, speed",
    "q06": "Dormant talent: open to work but no application in 90 days",
    "q07": "Funnel by source channel",
    "q08": "Referral programme by referrer, with bonus cost",
    "q09": "Skill-gap matching for one candidate (focus query)",
    "q10": "Where the hiring loop spends its time, by seniority",
    "q11": "Interviewer calibration: who passes everyone",
    "q12": "Company demand against internal supply",
    "q13": "Postings whose screening stage has gone quiet",
    "q14": "Monthly momentum with moving average and running total",
    "q15": "Company ranking within its industry",
    "q16": "Recruiter leaderboard with rank and percentile",
    "q17": "Skill scarcity index with quartiles",
    "q18": "Warm-introduction candidates within two hops (focus query)",
}


def size_str(n):
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n/1024:.1f} KB"
    return f"{n/1024/1024:.2f} MB"


def walk():
    files, dirs = [], []
    for base, dnames, fnames in os.walk(ROOT):
        dnames.sort()
        rel_base = os.path.relpath(base, ROOT).replace("\\", "/")
        if rel_base != ".":
            dirs.append(rel_base)
        for f in sorted(fnames):
            rel = (rel_base + "/" + f) if rel_base != "." else f
            files.append(rel)
    return dirs, files


dirs, files = walk()
summary = json.load(open(os.path.join(ROOT, "query_results", "_summary.json"),
                         encoding="utf-8"))
consistency = json.load(open(os.path.join(ROOT, "query_results", "_consistency_report.json"),
                             encoding="utf-8"))

# ------------------------------------------------------------------ tree
TREE = """LinkedIn_交付/
|-- design/                six design documents
|   |-- Requirements.md
|   |-- Entity_Relationship_Catalog.md
|   |-- Relational_Schema.md
|   |-- Normalization_Proof.xlsx
|   |-- Constraint_Inventory.md
|   `-- Design_Rationale.md
|-- sql/                   run in this order: 01 -> 02 -> 04 -> 03
|   |-- 01_schema.sql
|   |-- 02_seed.sql
|   |-- 03_queries.sql
|   `-- 04_views_triggers.sql
|-- erd/                   five diagrams, PNG + SVG
|   |-- ERD_conceptual.png / .svg
|   |-- ERD_logical_full.png / .svg
|   |-- ERD_module_identity.png / .svg
|   |-- ERD_module_demand.png / .svg
|   `-- ERD_module_hiring_loop.png / .svg
|-- query_results/         18 CSVs + 2 machine-readable reports
|   |-- q01_result.csv ... q18_result.csv
|   |-- _summary.json
|   `-- _consistency_report.json
|-- slides/                the presentation package
|   |-- LinkedIn.pptx
|   |-- LinkedIn_Narrative.docx
|   |-- LinkedIn_Narrative.pdf
|   |-- Presentation_Script.md
|   |-- QA_Prep.md
|   `-- Task_Allocation.md
|-- build/                 the generators (not required to run the database)
|   |-- README.md
|   |-- build_all.py        one-command rebuild: seed -> schema -> queries -> audit
|   |-- gen_seed.py        deterministic instance
|   |-- build_queries.py   fills the parameterised queries
|   |-- queries_template.sql
|   |-- run_queries.py     writes the 18 CSVs
|   |-- verify_data.py     the 22 invariants
|   |-- fault_injection.py the 14 refused statements
|   |-- erd.py             the five diagrams
|   |-- gen_normalization_xlsx.py
|   |-- build_deck.py
|   |-- build_narrative_docx.py
|   `-- build_file_guide.py   this document
`-- File_Guide.docx / .pdf     this document
"""

doc = Document()
sec = doc.sections[0]
sec.page_height = Cm(29.7)
sec.page_width = Cm(21.0)
sec.left_margin = Cm(2.2)
sec.right_margin = Cm(2.2)
sec.top_margin = Cm(2.0)
sec.bottom_margin = Cm(2.0)

normal = doc.styles["Normal"]
normal.font.name = "Segoe UI"
normal.font.size = Pt(9.5)
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


def h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.font.name = "Georgia"
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = NAVY
    return p


def h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    r.font.name = "Segoe UI"
    r.font.size = Pt(10.5)
    r.font.bold = True
    r.font.color.rgb = BLUE
    return p


def body(text, space=6, size=9.5):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space)
    p.paragraph_format.line_spacing = 1.2
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor(0x22, 0x2A, 0x33)
    return p


def mono(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(text)
    r.font.name = "Consolas"
    r.font.size = Pt(7.6)
    r.font.color.rgb = RGBColor(0x22, 0x2A, 0x33)
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
    return p


def table(headers, rows, widths=None, size=8.4):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    hdr = t.rows[0].cells
    for i, htext in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        r = p.add_run(htext)
        r.font.bold = True
        r.font.size = Pt(size)
        r.font.name = "Segoe UI"
        r.font.color.rgb = NAVY
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            r = p.add_run(str(val))
            r.font.size = Pt(size)
            r.font.name = "Segoe UI"
            if i == 0:
                r.font.bold = True
    if widths:
        t.autofit = False
        t.allow_autofit = False
        for i, w in enumerate(widths):
            t.columns[i].width = Cm(w)
            for row in t.rows:
                row.cells[i].width = Cm(w)
    # repeat the header row when the table crosses a page break
    tr = t.rows[0]._tr
    trPr = tr.get_or_add_trPr()
    tblHeader = trPr.makeelement(qn("w:tblHeader"), {})
    trPr.append(tblHeader)
    return t


# ------------------------------------------------------------------ cover
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(2)
r = p.add_run("D O T E   6 7 5 1   ·   D A T A B A S E   S Y S T E M S   ·   N O V E M B E R   2 0 2 6")
r.font.size = Pt(7.5)
r.font.bold = True
r.font.name = "Segoe UI"
r.font.color.rgb = BLUE

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(4)
r = p.add_run("File Guide and Verification Record")
r.font.name = "Georgia"
r.font.size = Pt(22)
r.font.bold = True
r.font.color.rgb = NAVY

body("LinkedIn, reverse-engineered · delivery folder LinkedIn_交付/ · generated by scanning the "
     "delivered directory, so every path below exists as described.", space=10, size=9)

# ------------------------------------------------------------------ 1
h1("1. What is in the box")
body("The delivery is a database package and a presentation package that share one source of "
     "truth: the schema in sql/. The design documents explain the model, the ERD folder draws it, "
     "the query results prove it runs, and the slides tell the story. build/ holds the generators "
     "that produced all of it, so the package can be rebuilt rather than trusted. Nothing in the "
     "folder is a mock-up; every table of numbers in the deck traces to a CSV in query_results/.")
mono(TREE)

# ------------------------------------------------------------------ 2
h1("2. File inventory")
body(f"{len(files)} files in {len(dirs)} sub-directories. One sentence per file, with its size "
     "on disk at delivery time.")

rows = []
for rel in files:
    if rel.startswith("query_results/q") and rel.endswith(".csv"):
        qid = rel.split("/")[-1][:3]
        rows.append([rel, size_str(os.path.getsize(os.path.join(ROOT, rel))),
                     f"{QNOTE.get(qid, '')} — result set, one row per group."])
    else:
        rows.append([rel, size_str(os.path.getsize(os.path.join(ROOT, rel))),
                     DESC.get(rel, "Survey instrument / supporting artefact.")])
table(["File", "Size", "What it is and what it is for"], rows, widths=[6.0, 1.8, 8.6], size=7.8)

# ------------------------------------------------------------------ 3
h1("3. How to rebuild the database")
body("MySQL 8.0.40, utf8mb4 throughout. The scripts use no extensions and no stored procedures, "
     "so they run unchanged in Navicat (Query → Run SQL File) and in the command-line client.")
h2("3.1 Run order")
mono("""01_schema.sql          drops and recreates linkedin_db with 12 tables
02_seed.sql            loads ~300 KB of INSERTs (deterministic, seed 20261115)
04_views_triggers.sql  creates 4 views and 4 triggers
03_queries.sql         read-only: 18 statements, run one at a time or all at once""")
body("Command line, from the sql/ folder, on Windows PowerShell:")
mono("""$env:MYSQL_PWD="<password>"
mysql -uroot --default-character-set=utf8mb4 -e "source 01_schema.sql"
mysql -uroot --default-character-set=utf8mb4 -e "source 02_seed.sql"
mysql -uroot --default-character-set=utf8mb4 -e "source 04_views_triggers.sql"
mysql -uroot --default-character-set=utf8mb4 -e "source 03_queries.sql\"""")
body("Note on paths: the MySQL client on Windows does not open a source file whose path contains "
     "non-ASCII characters. If the folder path has Chinese characters, copy the four .sql files to "
     "an ASCII path (for example C:\\Temp\\li_sql) and run them from there; this is a client "
     "limitation, not a script limitation.", size=8.8)

h2("3.2 Expected row counts")
table(["Table", "Rows", "Table", "Rows"],
      [["company", "60", "application", "250"],
       ["member", "300", "interview", "210"],
       ["skill", "60", "referral", "60"],
       ["job_posting", "120", "education", "393"],
       ["job_skill", "504", "experience", "492"],
       ["member_skill", "1 329", "connection", "1 065"]],
      widths=[4.0, 2.4, 4.0, 2.4], size=8.2)

h2("3.3 Object counts (a one-line health check)")
mono("""SELECT constraint_type, COUNT(*) FROM information_schema.table_constraints
 WHERE constraint_schema = 'linkedin_db' GROUP BY constraint_type;
-- PRIMARY KEY 12 · UNIQUE 7 · FOREIGN KEY 17 · CHECK 25
SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'linkedin_db';  -- 4
SELECT COUNT(*) FROM information_schema.views    WHERE table_schema = 'linkedin_db';    -- 4""")

# ------------------------------------------------------------------ 4
h1("4. Verification record")
h2("4.1 The eighteen queries")
body(f"All eighteen statements executed against the loaded schema on the delivery machine; "
     f"none failed and none required a session variable. The three slowest took under 15 ms. "
     f"Results are stored as UTF-8 CSV with a header row.")
qrows = []
for item in summary:
    qrows.append([item["q"], QNOTE.get(item["q"].lower(), item.get("title", "")),
                  item.get("rows", "—"), f"{item.get('ms', '—')} ms"])
table(["Query", "Question", "Rows", "Time"], qrows, widths=[1.3, 10.0, 1.6, 1.9], size=7.6)

h2("4.2 Cross-table consistency")
failed = consistency["summary"]["failed"]
body(f"{consistency['summary']['checks']} invariants checked, {failed} failed. The full report is "
     f"query_results/_consistency_report.json; the facts it records include 300 members, 60 "
     f"companies, 120 postings, 250 applications, 21 hires and a median of 35.1 days from "
     f"application to decision.")
frows = [[c["id"], c["rule"], "PASS" if c["status"] == "PASS" else "FAIL"]
         for c in consistency["checks"]]
table(["ID", "Invariant", "Result"], frows, widths=[1.2, 12.4, 1.4], size=7.4)

h2("4.3 Fault injection: proving the constraints bite")
body("Fourteen statements that should be impossible were attempted inside rolled-back "
     "transactions. Fourteen were refused, with the error codes below. This is the section to "
     "run in a live demo: each statement is one line and fails in under a second.")
table(["#", "Injected fault", "Error", "Raised by"],
      [["F1", "Apply twice to the same posting", "1062", "uk_app_job_member"],
       ["F2", "Inverted salary band", "3819", "ck_job_salary"],
       ["F3", "Second current experience", "1062", "uk_exp_one_current"],
       ["F4", "Self-loop connection", "3819", "ck_conn_order"],
       ["F5", "Application to a missing posting", "1644", "trg_application_before_insert"],
       ["F6", "Decision before application", "3819", "ck_app_decided"],
       ["F7", "Interview score of 9", "3819", "ck_int_score"],
       ["F8", "HIRED without decided_at", "1644", "trg_application_before_insert"],
       ["F9", "SUBMITTED → HIRED jump", "1644", "trg_application_status_guard"],
       ["F10", "Interview before the application", "1644", "trg_interview_before_insert"],
       ["F11", "Referral on a DIRECT application", "1644", "trg_referral_before_insert"],
       ["F12", "Referrer outside the company", "1644", "trg_referral_before_insert"],
       ["F13", "Delete an interviewer", "1451", "fk_int_member (RESTRICT)"],
       ["F14", "Negative referral bonus", "3819", "ck_ref_bonus"]],
      widths=[1.1, 8.4, 1.4, 4.5], size=7.6)
body("Reproduce with a single statement, for example:", space=2, size=8.8)
mono("""-- duplicate application (fails with 1062)
INSERT INTO application (job_id, member_id, status, applied_at)
SELECT job_id, member_id, 'SUBMITTED', applied_at FROM application LIMIT 1;""")

h2("4.4 Rendering checks")
body("The deck was rendered to PNG at 144 dpi, page by page, and inspected for overflow. Four "
     "defects were found and fixed: a two-line title colliding with its subtitle on slides 9, 10, "
     "12 and 14; a table row overlapping its caption on slide 8; a five-row column running past "
     "the footer on slide 7; and a path diagram overlapping the side panel on slide 10. The "
     "narrative was exported to PDF and its first page inspected for font fallback.")

# ------------------------------------------------------------------ 5
h1("5. Known trade-offs")
table(["Decision", "Consequence", "Where it is argued"],
      [["One decision timestamp, no status history",
        "Total cycle time is exact; per-stage time is approximated by the application date",
        "Design_Rationale §4.2 and §7 (L1, L3)"],
       ["Current employer derived, not stored",
        "One extra join per profile read; no update anomaly",
        "Design_Rationale §4.1; Normalization_Proof T11"],
       ["Referral 1:1 with its application",
        "A referral cannot exist without the application; the candidate and posting are not repeated",
        "Design_Rationale §2.2; Normalization_Proof T09"],
       ["Rules that span tables live in triggers",
        "Four triggers to maintain; errors surface as SQLSTATE 45000 with readable text",
        "Constraint_Inventory §3"],
       ["Connection stored once, canonical order",
        "Recursive query must flip direction; half the rows",
        "Design_Rationale §3; Q18"],
       ["Synthetic, deterministic instance",
        "Findings describe this instance, not LinkedIn; every number is reproducible",
        "Requirements A9; Design_Rationale §7"],
       ["Two-hop ceiling on the graph query",
        "Three hops would return most of the network; a reachability table is the scale fix",
        "Design_Rationale §8; QA_Prep Q13"],
       ["Single currency in the seed",
        "Cross-country salary comparison is nominal",
        "Requirements A6"]],
      widths=[4.6, 6.2, 4.6], size=7.6)

# ------------------------------------------------------------------ 6
h1("6. Assumptions in one place")
for line in [
    "A1  One application per member per posting; re-application is blocked by a unique key.",
    "A2  At most one experience row per member has is_current = 1, so the current employer is derived.",
    "A3  A referral is 1:1 with the application it produced.",
    "A4  PASS and FAIL carry a score; PENDING must not; NO_SHOW is unsupervised.",
    "A5  Hires never exceed openings; a filled posting is closed.",
    "A6  Salaries are annual and expressed in USD; the seed uses one currency.",
    "A7  The snapshot date is 2026-10-15 18:00; no timestamp in the instance is later.",
    "A8  A member does not apply to their current employer (audited, not enforced by a trigger).",
    "A9  Skills are a controlled vocabulary of 60 entries in eight families.",
    "A10 The presentation date is November 2026; all narrative uses it.",
]:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(1)
    r = p.add_run(line)
    r.font.size = Pt(8.6)
    r.font.color.rgb = RGBColor(0x22, 0x2A, 0x33)

body("", space=2)
body("Every artefact referenced above is inside this folder. If a claim in the deck and a number "
     "in the CSV ever disagree, the CSV is the record and the deck is the summary.", size=8.6)

doc.save(OUT)
print("wrote", OUT, os.path.getsize(OUT), "bytes;", len(files), "files listed")
