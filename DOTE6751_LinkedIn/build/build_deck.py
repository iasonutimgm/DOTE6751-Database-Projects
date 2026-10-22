# -*- coding: utf-8 -*-
"""Build slides/LinkedIn.pptx — 14 slides, 16:9, navy/white business-school style."""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

OUT = r"D:\桌面\数据库大作业\LinkedIn_交付\slides\LinkedIn.pptx"
ERD = r"D:\桌面\数据库大作业\LinkedIn_交付\erd"

NAVY = RGBColor(0x0E, 0x2A, 0x47)
BLUE = RGBColor(0x0A, 0x66, 0xC2)
GRAY = RGBColor(0x5A, 0x6B, 0x7B)
LGRAY = RGBColor(0x8A, 0x99, 0xA6)
PALE = RGBColor(0xF3, 0xF7, 0xFA)
BAR = RGBColor(0xDC, 0xE5, 0xEE)
RULE = RGBColor(0xD8, 0xE0, 0xE8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
AMBER = RGBColor(0xA6, 0x74, 0x1F)
GREEN = RGBColor(0x2E, 0x6B, 0x4F)

FONT_H = "Georgia"
FONT_B = "Segoe UI"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

SLIDES = []


def new_slide(notes=""):
    s = prs.slides.add_slide(BLANK)
    SLIDES.append((s, notes))
    return s


def tx(slide, x, y, w, h, text, size, color, bold=False, font=FONT_B,
       align=PP_ALIGN.LEFT, spacing=1.0, anchor=MSO_ANCHOR.TOP, space_after=0):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_before = Pt(0)
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = font
        r.font.color.rgb = color
    return box


def rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, radius=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    for style in s._element.findall(qn("p:style")):
        s._element.remove(style)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    if s.has_text_frame:
        s.text_frame.word_wrap = True
        s.text_frame.margin_left = 0
        s.text_frame.margin_right = 0
        s.text_frame.margin_top = 0
        s.text_frame.margin_bottom = 0
    return s


def header(slide, num, section, title, subtitle=None):
    tx(slide, 0.75, 0.40, 9.0, 0.30, f"{num:02d}  ·  {'  '.join(section.upper())}",
       9.5, BLUE, bold=True)
    tx(slide, 0.75, 0.68, 11.6, 0.80, title, 28, NAVY, bold=True, font=FONT_H)
    if subtitle:
        tx(slide, 0.75, 1.50, 11.2, 0.34, subtitle, 12, GRAY)
    rect(slide, 0.75, 2.00, 11.83, 0.012, RULE)


def footer(slide, num, total=14):
    rect(slide, 0.75, 6.98, 11.83, 0.010, RULE)
    tx(slide, 0.75, 7.05, 8.6, 0.22,
       "DOTE 6751  ·  Group Project  ·  LinkedIn, reverse-engineered  ·  November 2026",
       8, LGRAY)
    tx(slide, 10.6, 7.05, 2.0, 0.22, f"{num:02d} / {total}", 8, LGRAY, align=PP_ALIGN.RIGHT)


def row_table(slide, x, y, widths, rows, header_row=None, row_h=0.34, size=9,
              head_size=8, align=None, bold_col=None, zebra=True):
    """Draw a table out of shapes so the styling is fully controlled."""
    cy = y
    if header_row:
        rect(slide, x, cy, sum(widths), row_h, NAVY)
        cx = x
        for w, cell in zip(widths, header_row):
            tx(slide, cx + 0.10, cy + 0.07, w - 0.16, row_h - 0.08, cell, head_size,
               WHITE, bold=True)
            cx += w
        cy += row_h
    for i, row in enumerate(rows):
        if zebra and i % 2 == 1:
            rect(slide, x, cy, sum(widths), row_h, PALE)
        cx = x
        for j, (w, cell) in enumerate(zip(widths, row)):
            is_bold = (bold_col is not None and j == bold_col)
            a = PP_ALIGN.LEFT if align is None else align[j]
            tx(slide, cx + 0.10, cy + 0.075, w - 0.16, row_h - 0.08, str(cell), size,
               NAVY if is_bold else GRAY, bold=is_bold, align=a)
            cx += w
        cy += row_h
    return cy


def chip(slide, x, y, w, big, small, color=BLUE):
    rect(slide, x, y, w, 0.74, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.08)
    tx(slide, x + 0.22, y + 0.08, w - 0.3, 0.34, big, 15, color, bold=True)
    tx(slide, x + 0.22, y + 0.44, w - 0.3, 0.22, small.upper(), 7.5, LGRAY)


def picture(slide, path, x, y, w=None, h=None):
    if w:
        slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w))
    else:
        slide.shapes.add_picture(path, Inches(x), Inches(y), height=Inches(h))


# =====================================================================
# 1. Title
# =====================================================================
s = new_slide(
    "Good morning. This is our reverse-engineering project on LinkedIn. "
    "We did not have access to any schema; we reconstructed the part of LinkedIn that "
    "turns a job posting into a hire, and then built the database that would have to "
    "exist for the product's own behaviour to be possible. "
    "The deliverable has three parts: a twelve-table logical schema in third normal form, "
    "a deterministic data set of three hundred members and two hundred and fifty "
    "applications, and eighteen queries that answer questions the product visibly answers. "
    "I will take about three minutes on the model, then hand over to the query walk-through.")
rect(s, 0, 0, 13.333, 0.10, NAVY)
tx(s, 0.75, 0.75, 9.0, 0.30, "D O T E   6 7 5 1   ·   D A T A B A S E   S Y S T E M S   ·   G R O U P   P R O J E C T",
   9.5, BLUE, bold=True)
tx(s, 0.75, 1.22, 6.7, 1.55, "Reverse-Engineering\nLinkedIn", 38, NAVY, bold=True,
   font=FONT_H, spacing=1.06)
tx(s, 0.75, 2.86, 6.35, 0.90,
   "The hiring loop as a relational schema: twelve tables,\none closed loop, eighteen queries that the product "
   "answers but never shows.",
   12.5, GRAY, spacing=1.25)
rect(s, 0.75, 3.92, 3.2, 0.035, BLUE)
tx(s, 0.75, 4.18, 6.0, 0.26, "T E A M", 8.5, LGRAY, bold=True)
tx(s, 0.75, 4.48, 6.4, 0.80,
   "Xuanmo AN  ·  Yi HOU  ·  Zhao Han HUANG\nJinyu LI  ·  Yitong NI  ·  Shujing YE  ·  Shiyao ZHANG",
   11, NAVY, spacing=1.35)
tx(s, 0.75, 5.36, 6.0, 0.26, "D A T E", 8.5, LGRAY, bold=True)
tx(s, 0.75, 5.66, 4.0, 0.30, "November 2026", 12, NAVY)
# right: schema thumbnail
picture(s, os.path.join(ERD, "ERD_conceptual.png"), 7.55, 1.02, w=5.15)
tx(s, 7.55, 4.62, 5.15, 0.26, "Conceptual model — Chen notation", 8, LGRAY, align=PP_ALIGN.CENTER)
chip(s, 7.55, 5.02, 1.55, "12", "relations")
chip(s, 9.22, 5.02, 1.55, "17", "foreign keys")
chip(s, 10.89, 5.02, 1.60, "18", "queries")
tx(s, 7.55, 5.96, 5.15, 0.60,
   "A schema reverse-engineered from behaviour: every table\nexists because a product screen implies it.",
   8.6, GRAY, spacing=1.2)
footer(s, 1)

# =====================================================================
# 2. Motivation
# =====================================================================
s = new_slide(
    "Three observations motivated the scope. First, the product only ever shows outcomes: "
    "a filled role, a new hire badge. The two hundred and fifty applications behind that "
    "outcome are invisible, which is exactly the data a database course should model. "
    "Second, referrals are the channel every recruiter claims to value, and almost nobody "
    "can quantify; our funnel shows a threefold difference in end-to-end hire rate between "
    "referral and direct applications on the same data. Third, skill shortages are usually "
    "asserted in strategy documents; with postings and profiles in one schema they become "
    "computable. Those three observations are the spine of the eighteen queries.")
header(s, 2, "Motivation", "The visible product is the tip of an invisible record",
       "Every screen LinkedIn shows is the output of a join that the user never sees.")
left = [
    ("01", "Outcomes are visible, process is not",
     "A filled role is a badge. The 250 applications, 210 interviews and 12 legal status\n"
     "transitions behind it are not shown anywhere — and they are the interesting data."),
    ("02", "Referrals are praised, rarely measured",
     "Every recruiter says referrals convert. Without a channel column on the application,\n"
     "the claim cannot be tested. Here it can: 16.7% versus 5.3% end-to-end."),
    ("03", "Skill shortages are asserted, not computed",
     "Postings state requirements; profiles state holdings. Put both in one schema and the\n"
     "gap becomes a join, not an opinion."),
]
y = 2.28
for num, head, desc in left:
    tx(s, 0.75, y, 0.42, 0.34, num, 10, BLUE, bold=True)
    tx(s, 1.22, y - 0.02, 6.4, 0.30, head, 13.5, NAVY, bold=True)
    tx(s, 1.22, y + 0.30, 6.3, 0.78, desc, 9.5, GRAY, spacing=1.18)
    y += 1.28

chip(s, 7.95, 2.34, 2.2, "250", "applications seeded")
chip(s, 10.30, 2.34, 2.2, "8.4%", "reach hire")
chip(s, 7.95, 3.22, 2.2, "3.1×", "referral advantage")
chip(s, 10.30, 3.22, 2.2, "6.0", "months of history")
tx(s, 7.95, 4.30, 4.55, 0.24, "W H A T   W E   B U I L T", 8, LGRAY, bold=True)
tx(s, 7.95, 4.60, 4.55, 1.9,
   "A logical schema derived from the product's behaviour, a deterministic instance of it, "
   "and eighteen queries. The schema is in third normal form; the instance passes 22 "
   "cross-table consistency checks; every query runs standalone in Navicat.",
   9.5, GRAY, spacing=1.25)
footer(s, 2)

# =====================================================================
# 3. Business context
# =====================================================================
s = new_slide(
    "This is the loop we modelled. A recruiter creates a posting and declares the skills it "
    "requires. A member applies through one of three channels; the channel is a column on "
    "the application, not a separate table, because it describes how this application "
    "arrived. The recruiter screens, interviews are scheduled in rounds, and the application "
    "ends in exactly one of three terminal states. Each arrow on the left writes a specific "
    "row, which is the point of the slide: the diagram is a data-flow diagram as much as a "
    "process diagram. The state machine on the right is enforced by a trigger, so an "
    "application cannot jump from submitted to hired.")
header(s, 3, "Business context", "How a hire happens — and which row each step writes",
       "Six steps, three channels, one state machine. The schema follows the rows, not the screens.")
steps = [
    ("1", "COMPANY POSTS", "job_posting + job_skill\nskills, seniority, band, openings"),
    ("2", "MEMBER APPLIES", "application\nchannel ∈ {direct, referral, sourcing}"),
    ("3", "RECRUITER SCREENS", "application.status = SCREENING\nor REJECTED / WITHDRAWN"),
    ("4", "INTERVIEWS RUN", "interview, rounds 1..n\ninterviewer, outcome, score"),
    ("5", "OFFER AND DECISION", "status → OFFER → HIRED / REJECTED\ndecided_at is stamped"),
    ("6", "REFERRAL SETTLES", "referral.bonus_status\nPENDING → PAID / FORFEITED"),
]
y = 2.24
for num, head, desc in steps:
    if int(num) < 6:
        rect(s, 0.94, y + 0.36, 0.012, 0.62, RULE)
    c = rect(s, 0.77, y + 0.02, 0.34, 0.34, NAVY, MSO_SHAPE.OVAL)
    tf = c.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = num
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.name = FONT_B
    r.font.color.rgb = WHITE
    tx(s, 1.28, y, 3.4, 0.24, head, 10, NAVY, bold=True)
    tx(s, 1.28, y + 0.25, 4.6, 0.56, desc, 8.5, GRAY, spacing=1.15)
    y += 0.78

CARD_X, CARD_Y, CARD_W, CARD_H = 6.55, 2.24, 5.95, 4.18
rect(s, CARD_X, CARD_Y, CARD_W, CARD_H, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
tx(s, CARD_X + 0.30, CARD_Y + 0.18, 5.2, 0.22, "S T A T E   M A C H I N E   ·   A P P L I C A T I O N",
   8, LGRAY, bold=True)
states = ["SUBMITTED", "SCREENING", "INTERVIEW", "OFFER", "HIRED"]
xx = CARD_X + 0.30
for i, st in enumerate(states):
    w = 0.98 if st != "SCREENING" else 1.06
    fill = NAVY if st in ("SUBMITTED", "SCREENING", "INTERVIEW") else BLUE
    rect(s, xx, CARD_Y + 0.52, w, 0.32, fill, MSO_SHAPE.ROUNDED_RECTANGLE, 0.22)
    tx(s, xx, CARD_Y + 0.585, w, 0.20, st, 6.6, WHITE, bold=True, align=PP_ALIGN.CENTER)
    if i < len(states) - 1:
        tx(s, xx + w + 0.01, CARD_Y + 0.575, 0.12, 0.20, "›", 10, LGRAY, bold=True,
           align=PP_ALIGN.CENTER)
    xx += w + 0.14
tx(s, CARD_X + 0.30, CARD_Y + 0.98, 5.3, 0.24,
   "exit at any stage →  REJECTED   or   WITHDRAWN", 8.5, AMBER)
rect(s, CARD_X + 0.30, CARD_Y + 1.30, 5.35, 0.010, RULE)
tx(s, CARD_X + 0.30, CARD_Y + 1.42, 2.6, 0.22, "WHAT THE DATABASE REFUSES", 8, LGRAY, bold=True)
rules = [
    "a jump from SUBMITTED straight to HIRED",
    "an interview before the application",
    "a second round numbered 2",
    "a referral from outside the company",
    "a terminal status without decided_at",
]
yy = CARD_Y + 1.72
for rtext in rules:
    tx(s, CARD_X + 0.30, yy, 0.16, 0.22, "·", 11, BLUE, bold=True)
    tx(s, CARD_X + 0.50, yy, 5.1, 0.22, rtext, 9, GRAY)
    yy += 0.30
tx(s, CARD_X + 0.30, CARD_Y + 3.32, 5.35, 0.62,
   "One BEFORE UPDATE trigger enforces all twelve legal transitions;\n"
   "three further triggers carry the cross-table rules.", 8.5, BLUE, spacing=1.2)
footer(s, 3)

# =====================================================================
# 4. ERD panorama
# =====================================================================
s = new_slide(
    "Here is the whole model. Twelve relations, seventeen foreign keys, twenty-five check "
    "constraints. Two things are worth pointing at. The member table is deliberately thin: "
    "there is no current-employer column, because that fact is already implied by the "
    "experience table with its single live row. And the application table is the hinge: "
    "everything on the left describes a person, everything on the bottom describes a "
    "decision, and the loop queries all join through it. The diagram is generated from the "
    "same table definitions that produce the DDL, so it cannot drift from the schema.")
header(s, 4, "Data model", "Twelve relations, one hinge",
       "Member and company describe the parties; application is the hinge that every query joins through.")
picture(s, os.path.join(ERD, "ERD_logical_full.png"), 0.75, 2.18, h=4.62)
tx(s, 0.75, 6.84, 4.6, 0.18, "ERD_logical_full — PK bold, FK italic, crow's foot at the many side",
   7.5, LGRAY)

RX = 5.72
tx(s, RX, 2.18, 6.8, 0.26, "W H A T   T H E   D I A G R A M   S A Y S", 8, LGRAY, bold=True)
points = [
    ("Two parties, one hinge",
     "member and company are the only entities that exist before a hire; application is the\n"
     "associative entity that records the encounter between them."),
    ("The current employer is derived",
     "no member.current_company_id: experience.is_current plus a unique index over a\n"
     "generated column guarantees exactly one live position per member."),
    ("Skills are relations, not text",
     "member_skill and job_skill carry proficiency and importance, which is what turns a\n"
     "keyword into a match score."),
    ("Referral is 1:1 with its application",
     "the referral table stores only the referrer and the bonus; the candidate and the posting\n"
     "are read through the application, so they cannot disagree."),
]
y = 2.52
for head, body in points:
    tx(s, RX, y, 0.14, 0.24, "—", 10, BLUE, bold=True)
    tx(s, RX + 0.22, y - 0.02, 5.9, 0.24, head, 11.5, NAVY, bold=True)
    tx(s, RX + 0.22, y + 0.26, 6.0, 0.62, body, 8.8, GRAY, spacing=1.15)
    y += 0.94

chip(s, RX, 6.22, 1.42, "12", "relations")
chip(s, RX + 1.52, 6.22, 1.42, "17", "foreign keys")
chip(s, RX + 3.04, 6.22, 1.42, "25", "check")
chip(s, RX + 4.56, 6.22, 1.55, "3NF", "proven per table")
footer(s, 4)

# =====================================================================
# 5. Module A
# =====================================================================
s = new_slide(
    "Module A is the person. Four tables hang off member: education, experience, connection "
    "and the skill claims. The design decision to highlight is the missing current-employer "
    "column. Storing it would duplicate a fact that experience already carries, and the two "
    "copies could disagree after an edit; that is the update anomaly the textbook warns "
    "about. Instead, is_current marks the live row, and a generated column with a unique "
    "index makes a second live row impossible. The connection table is the undirected social "
    "edge, stored once in canonical order, and it is what the recursive query on slide ten "
    "walks.")
header(s, 5, "Module A", "Identity: one person, four records around them",
       "Profile, credentials, history and graph — everything the product knows before a job exists.")
picture(s, os.path.join(ERD, "ERD_module_identity.png"), 0.75, 2.24, w=7.55)
tx(s, 0.75, 6.02, 7.55, 0.18, "ERD_module_identity", 7.5, LGRAY)

RX = 8.62
rect(s, RX, 2.22, 3.95, 4.30, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
tx(s, RX + 0.28, 2.40, 3.4, 0.22, "T H E   O N E   R E A L   D E C I S I O N", 7.5, LGRAY, bold=True)
tx(s, RX + 0.28, 2.68, 3.4, 0.30, "No current employer\ncolumn", 12.5, NAVY, bold=True,
   font=FONT_H, spacing=1.1)
tx(s, RX + 0.28, 3.36, 3.42, 1.75,
   "It is already implied by experience. Storing both creates a redundancy the DBMS cannot "
   "police: two rows, one fact, silent disagreement after an edit.", 8.6, GRAY, spacing=1.22)
rect(s, RX + 0.28, 4.42, 3.4, 0.010, RULE)
tx(s, RX + 0.28, 4.54, 3.36, 0.22, "IN STEAD", 7.5, LGRAY, bold=True)
tx(s, RX + 0.28, 4.80, 3.42, 0.95,
   "is_current = 1\n+ unique index on a generated column\n→ at most one live position",
   8.4, BLUE, spacing=1.2)
footer(s, 5)

# =====================================================================
# 6. Modules B and C
# =====================================================================
s = new_slide(
    "Modules B and C are the demand side and the loop. On the left, a company advertises "
    "postings and each posting declares the skills it wants with an importance flag. Notice "
    "that importance lives on job_skill, not on skill: the same skill is a hard requirement "
    "in one posting and a nice-to-have in another, which is precisely why the pair needs its "
    "own attribute. On the right, the application is at the centre, with interviews hanging "
    "off it and the referral attached one-to-one. The two modules meet at job_posting, which "
    "is why every funnel query starts there.")
header(s, 6, "Modules B and C", "Demand and decision: where the two halves meet",
       "A posting is a request for skills; an application is the answer to it.")
picture(s, os.path.join(ERD, "ERD_module_demand.png"), 0.75, 2.28, w=5.85)
tx(s, 0.75, 5.72, 5.85, 0.20, "ERD_module_demand — company, posting, skills",
   8, LGRAY)
tx(s, 0.75, 5.98, 5.85, 0.95,
   "importance lives on the pair, not on the skill: the same skill is REQUIRED here and\n"
   "PREFERRED there. That single attribute is what makes a match score defensible.",
   8.6, GRAY, spacing=1.2)

picture(s, os.path.join(ERD, "ERD_module_hiring_loop.png"), 6.95, 2.28, w=5.65)
tx(s, 6.95, 5.72, 5.65, 0.20, "ERD_module_hiring_loop — application, interview, referral",
   8, LGRAY)
tx(s, 6.95, 5.98, 5.65, 0.95,
   "interviews are numbered per application, not per posting; the referral is 1:1 with the\n"
   "application it produced, so its candidate and job cannot contradict it.",
   8.6, GRAY, spacing=1.2)
footer(s, 6)

# =====================================================================
# 7. The twelve tables
# =====================================================================
s = new_slide(
    "Twelve tables in three groups. The identity group is four tables around the person. The "
    "demand group is three tables: companies, postings and the skill vocabulary. The bottom "
    "group is the loop itself plus the two associative tables that connect people to skills "
    "and postings to skills. The counts are the seeded instance, and they matter: they are "
    "the evidence that the model is populated at a scale where the queries return "
    "distributions rather than anecdotes.")
header(s, 7, "The tables", "Twelve relations, three groups, one purpose each",
       "Counts are the seeded instance: large enough for distributions, small enough to audit by hand.")
groups = [
    ("IDENTITY", "4 tables", [
        ("member", "300", "the person; roles are relationships, not subtypes"),
        ("education", "393", "degrees, 1:N from member"),
        ("experience", "492", "employment history; one live row per member"),
        ("connection", "1 065", "undirected social edge, stored once"),
    ]),
    ("DEMAND", "3 tables", [
        ("company", "60", "employer facts stated once"),
        ("job_posting", "120", "one advertised opening, 4 lifecycle states"),
        ("skill", "60", "controlled vocabulary in 8 families"),
    ]),
    ("MATCHING & LOOP", "5 tables", [
        ("member_skill", "1 329", "proficiency 1–5, endorsements, years"),
        ("job_skill", "504", "REQUIRED vs PREFERRED, minimum level"),
        ("application", "250", "the state machine and its timestamps"),
        ("interview", "210", "rounds 1..n, outcome and score"),
        ("referral", "60", "1:1 with the application; bonus state"),
    ]),
]
x = 0.75
widths = [3.55, 3.55, 4.55]
for (gname, gcount, rows), w in zip(groups, widths):
    tx(s, x, 2.22, w - 0.2, 0.22, f"{gname}   ·   {gcount}", 8, BLUE, bold=True)
    pitch = 0.86 if len(rows) <= 4 else 0.79
    card_h = 0.74 if len(rows) <= 4 else 0.68
    y = 2.50
    for name, count, desc in rows:
        rect(s, x, y, w - 0.18, card_h, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.06)
        tx(s, x + 0.16, y + 0.09, 1.9, 0.22, name, 10, NAVY, bold=True)
        tx(s, x + w - 0.98, y + 0.09, 0.75, 0.22, count, 9, BLUE, bold=True, align=PP_ALIGN.RIGHT)
        tx(s, x + 0.16, y + 0.36, w - 0.52, 0.34, desc, 7.8, GRAY, spacing=1.08)
        y += pitch
    x += w
footer(s, 7)

# =====================================================================
# 8. Queries I — channel and referral
# =====================================================================
s = new_slide(
    "The first pair of queries is about where hires come from. On the left, the funnel by "
    "source channel. Referral applications are the smallest group, sixty of two hundred and "
    "fifty, but they produce almost half the hires: sixteen point seven percent end to end "
    "against five point three for direct. The interesting detail is that the interview rate "
    "is almost identical across channels; the difference is what happens after the "
    "interview, which is exactly the kind of finding a single table cannot show. On the "
    "right, the referral programme by referrer: who refers, who converts, and what the "
    "bonuses cost. Two hires from three referrals at Oracle is the top of that list.")
header(s, 8, "Evidence I", "Referral is not a nicer channel — it is a different funnel",
       "Same interview rate, three times the hire rate: the difference sits after the interview.")
tx(s, 0.75, 2.18, 5.7, 0.22, "Q07   ·   FUNNEL BY SOURCE CHANNEL", 8, BLUE, bold=True)
rows = [
    ["Referral", "60", "46.7%", "16.7%"],
    ["Sourcing", "40", "42.5%", "7.5%"],
    ["Direct", "150", "44.7%", "5.3%"],
]
row_table(s, 0.75, 2.46, [1.55, 1.35, 1.55, 1.55],
          rows, header_row=["Channel", "Applications", "Interview rate", "Hired"],
          row_h=0.36, size=9, head_size=8, bold_col=0,
          align=[PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT])
tx(s, 0.75, 3.98, 5.7, 0.55,
   "Interview rates differ by 4 points. Hire rates differ by 11.\n"
   "The leverage is in the interview-to-offer step, not in sourcing volume.",
   8.8, GRAY, spacing=1.2)
rect(s, 0.75, 4.56, 5.7, 0.010, RULE)
tx(s, 0.75, 4.66, 5.7, 0.22, "Q08   ·   REFERRER LEADERBOARD (TOP 4)", 8, BLUE, bold=True)
rows2 = [
    ["Noah Zhu · Oracle", "3", "2", "66.7%", "$8 500"],
    ["Nina Choi · OCBC", "2", "1", "50.0%", "$2 500"],
    ["Vikram Lin · Ping An", "1", "1", "100%", "$3 500"],
    ["James Yang · Sea", "1", "1", "100%", "$0"],
]
row_table(s, 0.75, 4.88, [2.15, 0.85, 0.75, 0.95, 1.05],
          rows2, header_row=["Referrer · employer", "Refs", "Hires", "Rate", "Paid"],
          row_h=0.34, size=8.5, head_size=7.5,
          align=[PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT])

# right panel: what it means
rect(s, 6.85, 2.18, 5.72, 2.30, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
tx(s, 7.12, 2.34, 5.2, 0.22, "W H Y   I T   M A T T E R S", 7.5, LGRAY, bold=True)
tx(s, 7.12, 2.60, 5.2, 1.72,
   "A referral is pre-screened by someone whose own reputation is at stake. The data shows "
   "where that advantage lands: referred candidates are not more likely to be interviewed, "
   "they are more likely to be offered once interviewed.\n\n"
   "That distinction is only visible because the channel is a column on the application and "
   "the interview is its own relation. One flat 'hired' flag would have hidden it.",
   9.2, GRAY, spacing=1.2)
rect(s, 6.85, 4.68, 5.72, 1.95, WHITE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
rect(s, 6.85, 4.68, 0.05, 1.95, BLUE)
tx(s, 7.10, 4.84, 5.2, 0.22, "THE COST OF THE PROGRAMME", 8, LGRAY, bold=True)
tx(s, 7.10, 5.12, 5.25, 1.30,
   "$14 000 paid and $7 000 pending across 60 referrals — and three hires that arrived "
   "without a bonus paid at all. Bonus policy is a decision the schema can price, and the "
   "three hires are the evidence that it is a choice rather than a rule.",
   8.8, NAVY, spacing=1.24)
footer(s, 8)

# =====================================================================
# 9. Queries II — skill gap (focus)
# =====================================================================
s = new_slide(
    "This is the first of our two focus queries. Q09 asks a narrow question: for one named "
    "candidate, which open roles do they half-qualify for, and what exactly is missing? The "
    "candidate is Priya Walker, a project manager at Siemens. Twenty-eight open postings "
    "where she holds at least two of the hard requirements. The query returns the match "
    "percentage and, more usefully, the names of the missing skills, because 'sixty-seven "
    "percent' is not actionable and 'you are missing statistical analysis' is. The filter "
    "requires at least half of the hard requirements, so the answer set is short enough to "
    "act on.")
header(s, 9, "Evidence II", "Skill-gap matching: name the missing skill",
       "Q09 · one candidate, twenty-eight half-matching roles, one actionable list.")
tx(s, 0.75, 2.16, 7.4, 0.22, "Q09   ·   OPEN ROLES WHERE THE CANDIDATE MEETS ≥ 50% OF HARD REQUIREMENTS",
   8, BLUE, bold=True)
rows = [
    ["6", "Merchant Manager", "Amazon", "2 / 3", "66.7%", "Negotiation"],
    ["31", "Growth Analyst", "Tencent", "2 / 3", "66.7%", "Statistical Analysis"],
    ["40", "Consultant", "McKinsey", "2 / 3", "66.7%", "Data Modelling"],
    ["43", "Technology Auditor", "Goldman Sachs", "2 / 3", "66.7%", "Python"],
    ["44", "Analyst", "JPMorgan Chase", "2 / 3", "66.7%", "Statistical Analysis"],
    ["47", "Analyst", "HSBC", "2 / 3", "66.7%", "Statistical Analysis"],
]
row_table(s, 0.75, 2.44, [0.55, 1.85, 1.75, 0.80, 0.95, 1.68],
          rows, header_row=["Job", "Title", "Company", "Held", "Match", "Missing"],
          row_h=0.34, size=8.6, head_size=7.6,
          align=[PP_ALIGN.RIGHT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.RIGHT,
                 PP_ALIGN.RIGHT, PP_ALIGN.LEFT])
tx(s, 0.75, 4.86, 7.4, 0.22, "Top 12 of the 28 qualifying roles, ordered by match percentage; the CSV holds these twelve rows", 7.2, LGRAY)
# bottom-left: the gap in one sentence
rect(s, 0.75, 5.22, 7.4, 1.42, WHITE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
rect(s, 0.75, 5.22, 0.05, 1.42, BLUE)
tx(s, 1.02, 5.36, 6.9, 0.22, "T H E   G A P ,   I N   O N E   S E N T E N C E", 7.5, LGRAY, bold=True)
tx(s, 1.02, 5.64, 6.95, 0.90,
   "Across the twelve closest roles, statistical analysis is the missing skill five times — "
   "one course would move the candidate from “half-qualified” to “qualified” on five postings.",
   9.4, NAVY, spacing=1.24)

# right: method card
rect(s, 8.55, 2.16, 4.05, 2.28, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
tx(s, 8.82, 2.32, 3.5, 0.22, "H O W   T H E   M A T C H   I S   B U I L T", 7.5, LGRAY, bold=True)
tx(s, 8.82, 2.60, 3.55, 1.70,
   "required ← job_skill WHERE importance = 'REQUIRED'\n"
   "held      ← member_skill WHERE proficiency ≥ minimum\n"
   "match %   = held ÷ required\n"
   "missing   ← required set minus held set",
   8.6, NAVY, spacing=1.5)
tx(s, 8.55, 4.58, 4.05, 0.22, "W H Y   I T   I S   H A R D", 7.5, LGRAY, bold=True)
tx(s, 8.55, 4.86, 4.05, 1.55,
   "Matching on the skill id alone overstates fit: a skill at proficiency 2 is not the same "
   "as the minimum 4 the posting asks for. The join carries the threshold, and that is why "
   "the match percentage is defensible.", 8.6, GRAY, spacing=1.22)
chip(s, 8.55, 6.28, 1.28, "28", "roles ≥ 50%")
chip(s, 9.93, 6.28, 1.35, "66.7%", "best match")
chip(s, 11.38, 6.28, 1.22, "1", "skill missing")
footer(s, 9)

# =====================================================================
# 10. Queries III — warm intro (focus)
# =====================================================================
s = new_slide(
    "The second focus query is the one we are proudest of. Q18 answers a question the "
    "product charges money for: who could introduce me to this hiring team? It walks the "
    "connection graph recursively, two hops from the employees of the hiring company, and "
    "crosses that reachable set with the posting's hard requirements. On the IBM delivery "
    "manager role there are thirty-three reachable people; fifteen survive the skill filter, "
    "and one of them is a single hop from an employee. The query is a recursive CTE plus an "
    "anti-join, and it is the reason the connection table stores edges once in canonical "
    "order.")
header(s, 10, "Evidence III", "Warm introductions in two hops",
       "Q18 · two hops of the social graph, crossed with the posting's hard requirements.")
# path visual
tx(s, 0.75, 2.14, 7.4, 0.22, "Q18   ·   JOB 79 · DELIVERY MANAGER · IBM", 8, BLUE, bold=True)
boxes = [
    (0.75, "CANDIDATE", "Grace Sun\n8 yrs · San Francisco"),
    (2.88, "1st DEGREE", "Clara Ma\nworks at IBM"),
    (5.01, "HIRING TEAM", "IBM · 6 employees\n5 hard requirements"),
]
for x, tag, body in boxes:
    rect(s, x, 2.46, 1.92, 1.02, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.05)
    tx(s, x + 0.14, 2.54, 1.70, 0.20, tag, 7, LGRAY, bold=True)
    tx(s, x + 0.14, 2.78, 1.70, 0.62, body, 8.2, NAVY, bold=True, spacing=1.12)
for x in (2.68, 4.81):
    tx(s, x, 2.80, 0.22, 0.24, "›", 14, BLUE, bold=True, align=PP_ALIGN.CENTER)

rows = [
    ["Grace Sun", "1", "Clara Ma", "2 / 5"],
    ["Lars Park", "2", "Nina Jones", "4 / 5"],
    ["Zhiwei Muller", "2", "Anna Walker", "4 / 5"],
    ["Isha Park", "2", "Nina Jones", "3 / 5"],
    ["Ananya Smith", "2", "Oscar He", "3 / 5"],
]
row_table(s, 0.75, 3.72, [1.75, 0.85, 1.75, 1.10],
          rows, header_row=["Candidate", "Degrees", "Bridge", "Required held"],
          row_h=0.32, size=8.4, head_size=7.4,
          align=[PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.LEFT, PP_ALIGN.RIGHT])
tx(s, 0.75, 5.72, 6.0, 0.22,
   "15 rows returned · 33 candidates reachable before the skill filter",
   8, GRAY)
chip(s, 0.75, 6.06, 1.70, "33", "reachable")
chip(s, 2.57, 6.06, 1.70, "15", "skill-qualified")
chip(s, 4.39, 6.06, 1.80, "≤ 2", "hops walked")

rect(s, 7.05, 2.14, 5.55, 4.44, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
tx(s, 7.32, 2.32, 5.0, 0.22, "T H E   Q U E R Y   I N   T H R E E   M O V E S", 7.5, LGRAY, bold=True)
moves = [
    ("Anchor", "employees of the hiring company: experience WHERE is_current = 1"),
    ("Recurse", "walk connection both ways, at most two hops, keep the minimum hop count"),
    ("Cross", "join member_skill against the posting's REQUIRED skills; anti-join on applications"),
]
yy = 2.66
for head, body in moves:
    tx(s, 7.32, yy, 0.95, 0.22, head, 8.5, BLUE, bold=True)
    tx(s, 8.30, yy - 0.01, 4.05, 0.62, body, 8.4, GRAY, spacing=1.18)
    yy += 0.72
rect(s, 7.32, 4.90, 5.0, 0.010, RULE)
tx(s, 7.32, 5.02, 5.0, 0.22, "W H Y   I T   M A T T E R S", 7.5, LGRAY, bold=True)
tx(s, 7.32, 5.30, 5.05, 1.45,
   "The graph is only walkable because an edge is stored once, as an ordered pair. With "
   "both directions stored, the recursion visits every node twice and the minimum-hop "
   "reduction returns the wrong bridge.", 8.5, GRAY, spacing=1.2)
footer(s, 10)

# =====================================================================
# 11. Queries IV — cycle time and calibration
# =====================================================================
s = new_slide(
    "The last pair is about the loop's cost and its fairness. On the left, where the time "
    "goes. Across seniority levels a hire takes twenty-nine to thirty-eight days; the bulk of "
    "it is not the interviews, it is the gap between them, eighteen days on average, which is "
    "scheduling latency rather than deliberation. On the right, interviewer calibration: "
    "pass rates range from zero to a hundred percent on four to six interviews each, which "
    "is a signal about the interviewers as much as about the candidates. Neither number "
    "exists in a schema that stores only the final hire.")
header(s, 11, "Evidence IV", "Cycle time and interviewer calibration",
       "Q10 · where the 30 days go.   Q11 · who passes everyone.")
tx(s, 0.75, 2.14, 5.6, 0.22, "Q10   ·   DAYS BY STAGE, PER HIRE", 8, BLUE, bold=True)
rows = [
    ["Mid", "5", "4.8", "16.2", "9.0", "30.0"],
    ["Senior", "8", "6.1", "15.9", "8.0", "30.0"],
    ["Lead", "3", "6.3", "18.0", "8.0", "32.7"],
    ["Principal", "2", "3.0", "15.0", "12.5", "30.5"],
    ["Junior", "2", "4.5", "18.5", "13.0", "36.0"],
]
row_table(s, 0.75, 2.42, [1.15, 0.60, 0.85, 1.00, 0.85, 0.75],
          rows, header_row=["Level", "Hires", "→ 1st iv.", "across iv.", "→ decision", "Total"],
          row_h=0.32, size=8.2, head_size=7.2,
          align=[PP_ALIGN.LEFT] + [PP_ALIGN.RIGHT] * 5)
tx(s, 0.75, 4.48, 5.6, 0.60,
   "Interviews themselves are cheap: 15–20 days of elapsed time across three or four "
   "rounds. Waiting between them is the cost.", 8.6, GRAY, spacing=1.18)

tx(s, 0.75, 5.16, 5.6, 0.22, "Q11   ·   INTERVIEWER PASS RATE (≥ 3 INTERVIEWS)", 8, BLUE, bold=True)
rows2 = [
    ["Felix Luo · Shopify", "3", "0%"],
    ["Arjun Muller · Meituan", "4", "50%"],
    ["Grace Wu · Salesforce", "4", "100%"],
    ["Hao Hall · Sea Group", "4", "100%"],
]
row_table(s, 0.75, 5.42, [2.55, 1.10, 1.10],
          rows2, header_row=["Interviewer · employer", "Rounds", "Pass rate"],
          row_h=0.29, size=8.2, head_size=7.2,
          align=[PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT])

rect(s, 6.75, 2.14, 5.82, 2.16, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
tx(s, 7.02, 2.30, 5.2, 0.22, "R E A D I N G   T H E   T W O   T O G E T H E R", 7.5, LGRAY, bold=True)
tx(s, 7.02, 2.56, 5.3, 1.60,
   "A process that spends half its life waiting for calendars is a scheduling problem, not "
   "a hiring problem. A process whose pass rate depends on who runs the round is a "
   "calibration problem. Both are measurable only because the interview is a relation with "
   "an interviewer and a timestamp — not a status on the application.", 9.0, GRAY, spacing=1.2)
rect(s, 6.75, 4.48, 5.82, 2.16, WHITE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
rect(s, 6.75, 4.48, 0.05, 2.16, BLUE)
tx(s, 7.02, 4.62, 5.2, 0.22, "T H E   A S S U M P T I O N   W E   M A D E", 7.5, LGRAY, bold=True)
tx(s, 7.02, 4.88, 5.3, 1.62,
   "Stage entry is approximated by the application date, because the schema keeps one "
   "decision timestamp rather than a transition log. That is honest for total cycle time and "
   "optimistic for per-stage time; adding application_status_history is the first item on "
   "our improvement list.", 9.0, GRAY, spacing=1.2)
footer(s, 11)

# =====================================================================
# 12. Improvements and limitations
# =====================================================================
s = new_slide(
    "What we would change. Three improvements we consider structural rather than cosmetic: a "
    "status history table, so that stage durations stop being an approximation; an offer "
    "table, because compensation above band is currently invisible; and soft deletes, "
    "because at the moment deleting a member destroys their applications and therefore the "
    "funnel history. The limitations on the right are ones we accepted knowingly: the "
    "synthetic data, the single currency, the missing education key, and the two-hop ceiling "
    "on the graph query. Each is recorded in the design rationale with the trade-off that "
    "produced it.")
header(s, 12, "Improvement", "What we would build next",
       "A limitation that is written down is a design decision; one that is discovered in the demo is a defect.")
tx(s, 0.75, 2.18, 5.6, 0.22, "W O U L D   B U I L D   N E X T", 8, BLUE, bold=True)
improvements = [
    ("Status history", "application_status_history replaces the single decided_at, so stage\n"
                       "durations stop being approximated by the application date."),
    ("Offer table", "base, bonus, currency and acceptance date — today an above-band offer is\n"
                    "invisible and the salary column stays the posting's plan."),
    ("Soft delete", "member.deleted_at plus RESTRICT on application.member_id: deleting a\n"
                    "person currently destroys their funnel history."),
]
y = 2.52
for head, body in improvements:
    rect(s, 0.75, y, 0.05, 0.78, BLUE)
    tx(s, 0.95, y - 0.02, 5.2, 0.24, head, 11, NAVY, bold=True)
    tx(s, 0.95, y + 0.24, 5.3, 0.62, body, 8.8, GRAY, spacing=1.18)
    y += 0.94

tx(s, 6.75, 2.18, 5.8, 0.22, "K N O W N   L I M I T A T I O N S", 8, AMBER, bold=True)
limits = [
    ("Synthetic instance", "distributions are plausible, not empirical; no public dump was used."),
    ("One currency", "salaries are annual USD; cross-country comparison is nominal."),
    ("Education key unenforced", "the same degree can be recorded twice."),
    ("Two-hop ceiling", "three hops would need a materialised reachability table or a graph store."),
    ("No stage log", "decided_at doubles as 'last change', which is exact for hires and soft\n"
                     "for withdrawals."),
]
y = 2.50
for head, body in limits:
    tx(s, 6.75, y, 0.16, 0.22, "·", 12, AMBER, bold=True)
    tx(s, 6.98, y - 0.01, 5.55, 0.24, head, 9.6, NAVY, bold=True)
    tx(s, 6.98, y + 0.22, 5.55, 0.56, body, 8.4, GRAY, spacing=1.15)
    y += 0.86

# bottom-left: the one we would fix first
rect(s, 0.75, 5.62, 5.55, 1.16, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
tx(s, 1.00, 5.74, 5.0, 0.22, "I F   W E   F I X E D   O N E   T H I N G", 7.5, LGRAY, bold=True)
tx(s, 1.00, 6.00, 5.1, 0.70,
   "Soft delete. Losing the applications of a departed member is a compliance problem "
   "before it is a modelling one.", 8.8, NAVY, spacing=1.18)
footer(s, 12)

# =====================================================================
# 13. Appendix — task allocation
# =====================================================================
s = new_slide(
    "The split. Every member carried a comparable load, eight to fourteen hours, with "
    "difficulty between three and five. The schema and the seed were done first because "
    "every other task depends on them; the queries were split by group so that two people "
    "could work in parallel on independent SQL files; the documents and the deck ran in "
    "parallel once the schema was frozen. The allocation is not a division of page count, it "
    "is a division of dependency: nothing could start before the schema existed, and "
    "everything after it could run concurrently.")
header(s, 13, "Appendix", "Task allocation and effort",
       "Seven members, four dependency layers: schema → seed → queries → documents and deck.")
rows = [
    ["Xuanmo AN", "1155260677", "Conceptual & logical E-R model; §6.7 reduction write-up", "5", "14"],
    ["Yi HOU", "1155261383", "DDL, constraints and triggers; fault-injection suite", "5", "13"],
    ["Zhao Han HUANG", "1155272384", "Deterministic seed generator; 22 consistency checks", "5", "12"],
    ["Jinyu LI", "1155261567", "Business queries Q07–Q13; CSV harness", "4", "11"],
    ["Yitong NI", "1155265810", "Advanced queries Q14–Q18 (CTE, window, recursion)", "5", "12"],
    ["Shujing YE", "1155261750", "Requirements, constraint inventory, normalisation workbook", "3", "9"],
    ["Shiyao ZHANG", "1155261823", "Deck, narrative, script, Q&A preparation", "4", "10"],
]
row_table(s, 0.75, 2.30, [2.05, 1.55, 5.55, 1.25, 0.95],
          rows, header_row=["Member", "Student ID", "Primary responsibility", "Difficulty", "Hours"],
          row_h=0.40, size=9.2, head_size=8,
          align=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.RIGHT])
tx(s, 0.75, 5.84, 11.4, 0.24,
   "Total 81 person-hours · average 11.6 h · no task below difficulty 3 · every member "
   "reviewed at least one artefact they did not author.", 8.2, GRAY)
chip(s, 0.75, 6.16, 2.55, "81 h", "total effort")
chip(s, 3.46, 6.16, 2.55, "7", "members")
chip(s, 6.17, 6.16, 2.75, "4", "dependency layers")
chip(s, 8.98, 6.16, 3.55, "0", "artefacts without an owner")
footer(s, 13)

# =====================================================================
# 14. Q&A backup
# =====================================================================
s = new_slide(
    "Backup slide. If the questions go to the model, the Chen diagram is here: twelve entity "
    "sets, fifteen relationship sets, with cardinality ratios on every edge. The five "
    "questions on the right are the ones we expect: why twelve tables, why no current "
    "employer column, why the referral is not a column on the application, whether the data "
    "is real, and what happens if a referrer leaves the company. Short answers are on the "
    "slide; the long answers are in the design documents and in the Q&A preparation file.")
header(s, 14, "Q&A", "Backup: the conceptual model",
       "Chen notation — entity rectangles, relationship diamonds, 1 / N cardinality.")
picture(s, os.path.join(ERD, "ERD_conceptual.png"), 0.75, 2.12, w=6.25)
tx(s, 0.75, 6.42, 6.25, 0.20, "ERD_conceptual — full resolution in erd/", 7.5, LGRAY)

qa = [
    ("Why twelve tables?", "One per entity set, plus two associative tables for skills. The\n"
                           "mapping is §6.7 applied literally; nothing is merged for convenience."),
    ("Why no current employer column?", "It is functionally determined by experience.is_current;\n"
                                        "storing both is an update anomaly waiting to happen."),
    ("Why is the referral not a column?", "It is 1:1 and optional. A nullable column would carry\n"
                                         "a second candidate key and allow a referral without an\n"
                                         "application."),
    ("Is the data real?", "No. It is synthetic but self-consistent: 22 cross-table checks pass,\n"
                         "and the generator is deterministic."),
    ("What if a referrer leaves?", "The referral row keeps its referrer; the bonus already paid is\n"
                                  "evidence. Eligibility is checked when the referral is created."),
]
y = 2.16
for q, a in qa:
    tx(s, 7.55, y, 5.05, 0.24, q, 9.4, NAVY, bold=True)
    tx(s, 7.55, y + 0.24, 5.05, 0.70, a, 8.2, GRAY, spacing=1.14)
    y += 0.94
footer(s, 14)

# ---------------------------------------------------------------- notes
for slide, note in SLIDES:
    if note:
        slide.notes_slide.notes_text_frame.text = note

os.makedirs(os.path.dirname(OUT), exist_ok=True)
prs.save(OUT)
print("wrote", OUT, os.path.getsize(OUT), "bytes,", len(prs.slides.__iter__.__self__._sldIdLst), "slides")
