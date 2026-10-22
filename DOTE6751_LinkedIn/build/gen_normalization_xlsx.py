# -*- coding: utf-8 -*-
"""Build design/Normalization_Proof.xlsx — one sheet per relation plus a
summary, an FD inventory and a sheet of judgement calls.

The proof method is the one in Silberschatz et al., Database System Concepts,
7th ed. §7.3.2: for every non-trivial FD X -> A that holds on R, either X is a
superkey of R, or A is a prime attribute.  BCNF (§7.3.1) is the stricter test:
every determinant is a superkey.
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = r"D:\桌面\数据库大作业\LinkedIn_交付\design\Normalization_Proof.xlsx"

NAVY = "0E2A47"
BLUE = "0A66C2"
PALE = "EAF1F8"
LIGHT = "F6F9FC"
AMBER = "FFF4DC"
GREEN = "E8F3E8"

THIN = Side(style="thin", color="C9D3DD")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

TABLES = [
    dict(
        name="member", sheet="T01 member",
        purpose="One natural person; recruiter, referrer, interviewer and candidate are roles over this entity.",
        attrs=[("member_id", "INT PK"), ("full_name", "VARCHAR(80)"), ("headline", "VARCHAR(140)"),
               ("email", "VARCHAR(120)"), ("country", "CHAR(2)"), ("city", "VARCHAR(60)"),
               ("years_experience", "TINYINT UNSIGNED"), ("open_to_work", "BOOLEAN"),
               ("profile_visibility", "ENUM(3)"), ("joined_at", "DATE")],
        keys="member_id (PK); email (UQ)",
        fds=[("member_id", "full_name, headline, email, country, city, years_experience, "
                           "open_to_work, profile_visibility, joined_at", "primary key"),
             ("email", "member_id, full_name, headline, country, city, years_experience, "
                       "open_to_work, profile_visibility, joined_at", "candidate key (uk_member_email)")],
        prime="member_id, email",
        notes="city does not determine country as a schema rule: city names repeat across "
              "countries. The seed happens to use a consistent mapping, which is a data fact, "
              "not an FD, and is therefore not used in the proof.",
    ),
    dict(
        name="company", sheet="T02 company",
        purpose="The employer; industry and head-count band describe the company once, not each posting.",
        attrs=[("company_id", "INT PK"), ("company_name", "VARCHAR(90)"), ("industry", "VARCHAR(60)"),
               ("hq_country", "CHAR(2)"), ("size_band", "ENUM(7)"), ("founded_year", "SMALLINT"),
               ("is_verified", "BOOLEAN")],
        keys="company_id (PK); company_name (UQ)",
        fds=[("company_id", "company_name, industry, hq_country, size_band, founded_year, is_verified",
              "primary key"),
             ("company_name", "company_id, industry, hq_country, size_band, founded_year, is_verified",
              "candidate key (uk_company_name)")],
        prime="company_id, company_name",
        notes="No non-key determinant exists. size_band and industry are independent facts; "
              "neither implies the other.",
    ),
    dict(
        name="job_posting", sheet="T03 job_posting",
        purpose="One advertised opening, owned by a company and posted by a recruiter.",
        attrs=[("job_id", "INT PK"), ("company_id", "INT FK"), ("recruiter_id", "INT FK"),
               ("title", "VARCHAR(120)"), ("seniority", "ENUM(7)"), ("employment_type", "ENUM(4)"),
               ("work_mode", "ENUM(3)"), ("city", "VARCHAR(60)"), ("country", "CHAR(2)"),
               ("salary_min", "INT"), ("salary_max", "INT"), ("currency", "CHAR(3)"),
               ("min_years_experience", "TINYINT"), ("openings", "TINYINT"),
               ("status", "ENUM(4)"), ("posted_at", "DATETIME"), ("closed_at", "DATETIME")],
        keys="job_id (PK)",
        fds=[("job_id", "all other attributes", "primary key")],
        prime="job_id",
        notes="recruiter_id does NOT determine company_id as a schema FD: a recruiter may change "
              "employer while the historical posting stays with the hiring company. If it were an "
              "FD, this relation would be in 3NF but not BCNF; because it is not, BCNF holds.",
    ),
    dict(
        name="skill", sheet="T04 skill",
        purpose="Controlled vocabulary of 60 skills in eight families.",
        attrs=[("skill_id", "INT PK"), ("skill_name", "VARCHAR(60)"), ("skill_family", "ENUM(8)"),
               ("is_emerging", "BOOLEAN")],
        keys="skill_id (PK); skill_name (UQ)",
        fds=[("skill_id", "skill_name, skill_family, is_emerging", "primary key"),
             ("skill_name", "skill_id, skill_family, is_emerging", "candidate key (uk_skill_name)")],
        prime="skill_id, skill_name",
        notes="Two candidate keys, both minimal; every determinant is a superkey.",
    ),
    dict(
        name="member_skill", sheet="T05 member_skill",
        purpose="M:N between member and skill, carrying the attributes of the claim.",
        attrs=[("member_id", "INT PK FK"), ("skill_id", "INT PK FK"), ("proficiency", "TINYINT"),
               ("years_used", "DECIMAL(3,1)"), ("endorsement_count", "SMALLINT"),
               ("added_at", "DATE")],
        keys="(member_id, skill_id) (PK)",
        fds=[("(member_id, skill_id)", "proficiency, years_used, endorsement_count, added_at",
              "primary key")],
        prime="member_id, skill_id",
        notes="Partial-dependency test (2NF): proficiency is not determined by member_id alone "
              "(a member has different levels in different skills) nor by skill_id alone (two "
              "members differ on the same skill). Transitive test: no non-key attribute determines "
              "another. Hence 3NF and BCNF.",
    ),
    dict(
        name="job_skill", sheet="T06 job_skill",
        purpose="M:N between posting and skill; importance distinguishes hard from preferred requirements.",
        attrs=[("job_id", "INT PK FK"), ("skill_id", "INT PK FK"), ("importance", "ENUM(2)"),
               ("min_proficiency", "TINYINT")],
        keys="(job_id, skill_id) (PK)",
        fds=[("(job_id, skill_id)", "importance, min_proficiency", "primary key")],
        prime="job_id, skill_id",
        notes="importance cannot migrate to job_posting (a posting has several skills with "
              "different importance) nor to skill (the same skill is REQUIRED in one posting and "
              "PREFERRED in another). Full-key dependency only.",
    ),
    dict(
        name="application", sheet="T07 application",
        purpose="Associative entity of applies; the spine of the hiring loop and the state machine.",
        attrs=[("application_id", "INT PK"), ("job_id", "INT FK"), ("member_id", "INT FK"),
               ("source_channel", "ENUM(3)"), ("status", "ENUM(7)"), ("applied_at", "DATETIME"),
               ("decided_at", "DATETIME"), ("resume_version", "VARCHAR(20)")],
        keys="application_id (PK); (job_id, member_id) (UQ)",
        fds=[("application_id", "job_id, member_id, source_channel, status, applied_at, decided_at, "
                                "resume_version", "primary key"),
             ("(job_id, member_id)", "application_id, source_channel, status, applied_at, decided_at, "
                                     "resume_version", "candidate key (uk_app_job_member)")],
        prime="application_id, job_id, member_id",
        notes="Two candidate keys. Every determinant is a superkey, so the relation is BCNF; the "
              "surrogate does not weaken the proof because the natural key is still enforced.",
    ),
    dict(
        name="interview", sheet="T08 interview",
        purpose="One round of one application, with interviewer, schedule and assessed outcome.",
        attrs=[("interview_id", "INT PK"), ("application_id", "INT FK"), ("round_no", "TINYINT"),
               ("interview_type", "ENUM(5)"), ("scheduled_at", "DATETIME"),
               ("duration_min", "SMALLINT"), ("interviewer_id", "INT FK"),
               ("outcome", "ENUM(4)"), ("score", "TINYINT NULL")],
        keys="interview_id (PK); (application_id, round_no) (UQ)",
        fds=[("interview_id", "application_id, round_no, interview_type, scheduled_at, duration_min, "
                              "interviewer_id, outcome, score", "primary key"),
             ("(application_id, round_no)", "interview_id, interview_type, scheduled_at, duration_min, "
                                            "interviewer_id, outcome, score",
              "candidate key (uk_int_app_round)")],
        prime="interview_id, application_id, round_no",
        notes="outcome and score depend on the round, not on the application: the same application "
              "has a PASS in round 1 and a PENDING in round 2. Storing them on application would "
              "be a 1NF violation as well as wrong.",
    ),
    dict(
        name="referral", sheet="T09 referral",
        purpose="A recommendation, 1:1 with the application it produced.",
        attrs=[("referral_id", "INT PK"), ("application_id", "INT FK UQ"), ("referrer_id", "INT FK"),
               ("relationship", "ENUM(5)"), ("referred_at", "DATETIME"),
               ("bonus_amount", "DECIMAL(10,2)"), ("bonus_status", "ENUM(4)")],
        keys="referral_id (PK); application_id (UQ)",
        fds=[("referral_id", "application_id, referrer_id, relationship, referred_at, bonus_amount, "
                             "bonus_status", "primary key"),
             ("application_id", "referral_id, referrer_id, relationship, referred_at, bonus_amount, "
                                "bonus_status", "candidate key (uk_ref_application, 1:1)")],
        prime="referral_id, application_id",
        notes="The rejected alternative stored job_id and member_id here as well. Those attributes "
              "are determined by application_id, so they would have created the transitive "
              "dependency application_id -> (job_id, member_id) with a non-key right-hand side: "
              "3NF violation. They are therefore absent.",
    ),
    dict(
        name="education", sheet="T10 education",
        purpose="Degrees a member records; 1:N from member.",
        attrs=[("education_id", "INT PK"), ("member_id", "INT FK"), ("school_name", "VARCHAR(100)"),
               ("degree", "ENUM(6)"), ("field_of_study", "VARCHAR(80)"),
               ("start_year", "SMALLINT"), ("end_year", "SMALLINT NULL")],
        keys="education_id (PK)",
        fds=[("education_id", "member_id, school_name, degree, field_of_study, start_year, end_year",
              "primary key")],
        prime="education_id",
        notes="Known gap: (member_id, school_name, degree, start_year) is a natural key that is not "
              "enforced, so a duplicate degree row is representable. Adding the unique constraint "
              "would not change the normal form.",
    ),
    dict(
        name="experience", sheet="T11 experience",
        purpose="Employment history; at most one row per member is the current position.",
        attrs=[("experience_id", "INT PK"), ("member_id", "INT FK"), ("company_id", "INT FK"),
               ("title", "VARCHAR(100)"), ("start_date", "DATE"), ("end_date", "DATE NULL"),
               ("is_current", "BOOLEAN"), ("current_member_id", "INT GENERATED")],
        keys="experience_id (PK); UNIQUE(current_member_id)",
        fds=[("experience_id", "member_id, company_id, title, start_date, end_date, is_current",
              "primary key")],
        prime="experience_id",
        notes="'is_current = 1 and member_id = x' determines at most one row: that is a uniqueness "
              "constraint (the generated-column index), not an FD with a non-key determinant, so "
              "it does not affect the normal form. title does not determine company_id: two "
              "engineers at two companies share a title.",
    ),
    dict(
        name="connection", sheet="T12 connection",
        purpose="Undirected social edge, stored once in canonical order.",
        attrs=[("member_a_id", "INT PK FK"), ("member_b_id", "INT PK FK"),
               ("connected_at", "DATETIME"), ("connection_type", "ENUM(4)")],
        keys="(member_a_id, member_b_id) (PK); CHECK (member_a_id < member_b_id)",
        fds=[("(member_a_id, member_b_id)", "connected_at, connection_type", "primary key")],
        prime="member_a_id, member_b_id",
        notes="The CHECK is part of the key semantics: without it the same undirected edge could "
              "appear twice and the 'primary key' would no longer identify the edge.",
    ),
]


def style_header(ws, row=1, cols=1):
    for c in range(1, cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(name="Segoe UI", bold=True, color="FFFFFF", size=10)
        cell.alignment = Alignment(vertical="center", horizontal="left")
    ws.row_dimensions[row].height = 22


def title_block(ws, title, subtitle):
    ws["A1"] = title
    ws["A1"].font = Font(name="Georgia", bold=True, size=15, color=NAVY)
    ws["A2"] = subtitle
    ws["A2"].font = Font(name="Segoe UI", size=9, color="5A6B7B")
    ws.row_dimensions[1].height = 24


def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w


def section(ws, row, text):
    ws.cell(row=row, column=1, value=text)
    ws.cell(row=row, column=1).font = Font(name="Segoe UI", bold=True, size=10, color=BLUE)
    return row + 1


wb = Workbook()

# ---------------------------------------------------------------- Summary
ws = wb.active
ws.title = "Summary"
title_block(ws, "Normalisation Proof — LinkedIn hiring-loop schema",
            "DOTE 6751 · November 2026 · method: Silberschatz et al., Database System Concepts 7e, §7.3.2 (3NF test) and §7.3.1 (BCNF)")
hdr = ["#", "Relation", "Primary key", "Candidate keys", "Attributes", "Non-trivial FDs",
       "3NF", "BCNF", "Decomposition needed"]
ws.append([])
ws.append(hdr)
for c in range(1, len(hdr) + 1):
    cell = ws.cell(row=4, column=c)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.font = Font(bold=True, color="FFFFFF", size=10)
    cell.alignment = Alignment(vertical="center", wrap_text=True)
ws.row_dimensions[4].height = 30

r = 5
for i, t in enumerate(TABLES, start=1):
    ws.cell(row=r, column=1, value=i)
    ws.cell(row=r, column=2, value=t["name"])
    ws.cell(row=r, column=3, value=t["keys"].split(";")[0].strip())
    ws.cell(row=r, column=4, value=t["keys"])
    ws.cell(row=r, column=5, value=len(t["attrs"]))
    ws.cell(row=r, column=6, value=len(t["fds"]))
    ws.cell(row=r, column=7, value="yes")
    ws.cell(row=r, column=8, value="yes")
    ws.cell(row=r, column=9, value="no")
    for c in range(1, 10):
        cell = ws.cell(row=r, column=c)
        cell.border = BORDER
        cell.alignment = Alignment(vertical="top", wrap_text=(c == 4))
        cell.font = Font(name="Segoe UI", size=10, bold=(c == 2))
        if i % 2 == 0:
            cell.fill = PatternFill("solid", fgColor=LIGHT)
    r += 1

ws.cell(row=r + 1, column=1, value="Verdict").font = Font(bold=True, color=NAVY, size=10)
ws.cell(row=r + 1, column=2,
        value="12 relations, 0 decompositions. Every non-trivial FD has a superkey on the left, "
              "so all relations satisfy BCNF, which implies 3NF. The stronger result is reported "
              "because it happened to hold; the design target was 3NF.").alignment = Alignment(wrap_text=True)
ws.merge_cells(start_row=r + 1, start_column=2, end_row=r + 3, end_column=9)
widths(ws, {"A": 9, "B": 16, "C": 36, "D": 46, "E": 11, "F": 14, "G": 9, "H": 9, "I": 19})
ws.freeze_panes = "A5"

# ---------------------------------------------------------------- Method
ws = wb.create_sheet("Method")
title_block(ws, "How the proof works", "The two tests applied to every relation")
lines = [
    ("1. Collect the FDs", "Read them off the E-R mapping: an FK gives no FD by itself; the FDs come "
                           "from the identifier of each entity set and from the natural keys the "
                           "business enforces (unique e-mail, unique company name, ...)."),
    ("2. Candidate keys", "A candidate key is a minimal determinant of all attributes. Where a UNIQUE "
                          "constraint exists, it is a candidate key by construction, because the DBMS "
                          "refuses any pair of rows that would violate it."),
    ("3. 2NF (no partial dependency)", "Only relevant for composite keys: member_skill, job_skill, "
                                       "interview, connection. For each, every non-prime attribute "
                                       "was tested against each key part separately."),
    ("4. 3NF test", "For every non-trivial FD X -> A: X is a superkey, or A is prime. A violation "
                    "would be a transitive dependency on a non-key determinant."),
    ("5. BCNF test", "For every non-trivial FD X -> A: X is a superkey. Strictly stronger; a relation "
                     "in BCNF is automatically in 3NF."),
    ("6. Decomposition", "Only needed where a test fails. None failed, so no decomposition is "
                         "proposed; the 3NF synthesis algorithm (§7.4) and BCNF decomposition "
                         "(§7.3.1) were not required."),
]
r = 4
for head, body in lines:
    ws.cell(row=r, column=1, value=head).font = Font(bold=True, size=10, color=BLUE)
    ws.cell(row=r, column=2, value=body).alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 46
    r += 1
widths(ws, {"A": 30, "B": 110})

# ---------------------------------------------------------------- FD inventory
ws = wb.create_sheet("FD_Inventory")
title_block(ws, "Functional dependency inventory", "Every FD used in the proof, with its source")
head = ["Relation", "FD", "Determinant type", "RHS prime?", "Source / justification"]
ws.append([])
ws.append(head)
for c in range(1, 6):
    cell = ws.cell(row=4, column=c)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.font = Font(bold=True, color="FFFFFF", size=10)
r = 5
for t in TABLES:
    for det, dep, why in t["fds"]:
        ws.cell(row=r, column=1, value=t["name"])
        ws.cell(row=r, column=2, value=f"{det} → {dep}")
        ws.cell(row=r, column=3, value="candidate key" if "candidate" in why or "primary" in why else "non-key")
        ws.cell(row=r, column=4, value="n/a")
        ws.cell(row=r, column=5, value=why)
        for c in range(1, 6):
            cell = ws.cell(row=r, column=c)
            cell.border = BORDER
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.font = Font(name="Segoe UI", size=9)
        r += 1
widths(ws, {"A": 16, "B": 80, "C": 18, "D": 10, "E": 40})
ws.freeze_panes = "A5"

# ---------------------------------------------------------------- per table
for t in TABLES:
    ws = wb.create_sheet(t["sheet"])
    title_block(ws, f"{t['name']}  —  3NF proof", t["purpose"])
    r = 4
    r = section(ws, r, "Attributes and domains")
    ws.cell(row=r, column=1, value="Attribute").font = Font(bold=True, size=9, color="FFFFFF")
    ws.cell(row=r, column=2, value="Domain").font = Font(bold=True, size=9, color="FFFFFF")
    ws.cell(row=r, column=1).fill = PatternFill("solid", fgColor=BLUE)
    ws.cell(row=r, column=2).fill = PatternFill("solid", fgColor=BLUE)
    r += 1
    for a, dom in t["attrs"]:
        ws.cell(row=r, column=1, value=a).font = Font(name="Segoe UI", size=9)
        ws.cell(row=r, column=2, value=dom).font = Font(name="Segoe UI", size=9, color="5A6B7B")
        r += 1
    r += 1
    r = section(ws, r, "Keys")
    ws.cell(row=r, column=1, value=t["keys"]).alignment = Alignment(wrap_text=True)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 28
    r += 2
    r = section(ws, r, "Functional dependencies")
    for h, c in (("Determinant", 1), ("Determines", 3), ("Why it holds", 5)):
        ws.cell(row=r, column=c, value=h).font = Font(bold=True, size=9, color="FFFFFF")
        ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=BLUE)
    r += 1
    for det, dep, why in t["fds"]:
        ws.cell(row=r, column=1, value=det).font = Font(name="Segoe UI", size=9, bold=True)
        ws.cell(row=r, column=3, value=dep).font = Font(name="Segoe UI", size=9)
        ws.cell(row=r, column=5, value=why).font = Font(name="Segoe UI", size=9, color="5A6B7B")
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=4)
        ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=8)
        ws.row_dimensions[r].height = 30
        r += 1
    r += 1
    r = section(ws, r, "3NF / BCNF test")
    checks = [
        ("Prime attributes", t["prime"]),
        ("2NF", "no partial dependency on a composite key" if "(" in t["keys"]
                else "single-attribute key, 2NF holds trivially"),
        ("3NF", "every non-trivial FD has a superkey on the left (or a prime RHS) — PASS"),
        ("BCNF", "every determinant is a candidate key — PASS"),
        ("Decomposition", "none required"),
    ]
    for k, v in checks:
        ws.cell(row=r, column=1, value=k).font = Font(bold=True, size=9, color=NAVY)
        ws.cell(row=r, column=2, value=v).font = Font(name="Segoe UI", size=9)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
        ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 26
        r += 1
    r += 1
    r = section(ws, r, "Judgement calls")
    ws.cell(row=r, column=1, value=t["notes"]).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r + 2, end_column=8)
    widths(ws, {"A": 26, "B": 22, "C": 16, "D": 14, "E": 22, "F": 16, "G": 14, "H": 12})

# ---------------------------------------------------------------- deviations
ws = wb.create_sheet("Judgement_Calls")
title_block(ws, "Judgement calls that a mechanical proof would get wrong",
            "Four places where the data looks like it implies an FD, and does not")
rows = [
    ("job_posting.recruiter_id", "Looks like recruiter_id → company_id",
     "A recruiter can change employer; the historical posting stays with the company that paid "
     "for it. Treating the pattern in the seed as an FD would make the relation 3NF but not BCNF."),
    ("member.headline", "Looks like member_id → company_name (via 'X at Y')",
     "headline is free text the member wrote. It is a snapshot, not a projection of experience; "
     "parsing it to recover the employer would be wrong and would break after a job change."),
    ("experience.is_current", "Looks like member_id → company_id",
     "Only true while is_current = 1. The fact is 'this row is the live one', enforced by a unique "
     "index over a generated column; it is not an FD on member."),
    ("education", "Looks like (member_id, school_name, degree) is the key",
     "It is a natural key in the data but is not enforced, so it is not used as a candidate key in "
     "the proof. Adding UNIQUE would make it one and would not change the normal form."),
]
ws.append([])
ws.append(["Attribute", "Pattern in the seed", "Why it is not an FD"])
for c in range(1, 4):
    cell = ws.cell(row=4, column=c)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.font = Font(bold=True, color="FFFFFF", size=10)
r = 5
for a, b, c in rows:
    ws.cell(row=r, column=1, value=a).font = Font(name="Segoe UI", size=9, bold=True)
    ws.cell(row=r, column=2, value=b).font = Font(name="Segoe UI", size=9)
    ws.cell(row=r, column=3, value=c).font = Font(name="Segoe UI", size=9)
    ws.cell(row=r, column=3).alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 52
    r += 1
widths(ws, {"A": 30, "B": 44, "C": 80})

from openpyxl.worksheet.properties import PageSetupProperties
for ws_ in wb.worksheets:
    ws_.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws_.page_setup.orientation = "landscape"
    ws_.page_setup.fitToWidth = 1
    ws_.page_setup.fitToHeight = 0
    ws_.print_options.horizontalCentered = True

wb.save(OUT)
print("wrote", OUT, os.path.getsize(OUT), "bytes", len(wb.sheetnames), "sheets")
print(wb.sheetnames)
