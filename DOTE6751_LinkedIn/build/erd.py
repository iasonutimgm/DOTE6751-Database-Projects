# -*- coding: utf-8 -*-
"""ER diagrams for the LinkedIn reverse-engineering deliverable.

Three artefacts:
  ERD_logical_full   every table, PK bold, FK italic, crow's foot at the many end
  ERD_module_*       three subject areas
  ERD_conceptual     Chen notation: entity rectangles, relationship diamonds, 1/N
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon

NAVY = "#0E2A47"
BLUE = "#0A66C2"
AMBER = "#A6741F"
GRAY = "#5A6B7B"
LGRAY = "#C9D3DD"
FONT = "DejaVu Sans"

TABLES = {
    "member": [("member_id", "PK"), ("full_name", ""), ("headline", ""), ("email", "UQ"),
               ("country", ""), ("city", ""), ("years_experience", ""), ("open_to_work", ""),
               ("profile_visibility", ""), ("joined_at", "")],
    "company": [("company_id", "PK"), ("company_name", "UQ"), ("industry", ""),
                ("hq_country", ""), ("size_band", ""), ("founded_year", ""), ("is_verified", "")],
    "job_posting": [("job_id", "PK"), ("company_id", "FK"), ("recruiter_id", "FK"), ("title", ""),
                    ("seniority", ""), ("employment_type", ""), ("work_mode", ""),
                    ("city", ""), ("country", ""), ("salary_min", ""), ("salary_max", ""),
                    ("currency", ""), ("min_years_experience", ""), ("openings", ""),
                    ("status", ""), ("posted_at", ""), ("closed_at", "")],
    "skill": [("skill_id", "PK"), ("skill_name", "UQ"), ("skill_family", ""), ("is_emerging", "")],
    "member_skill": [("member_id", "PK FK"), ("skill_id", "PK FK"), ("proficiency", ""),
                     ("years_used", ""), ("endorsement_count", ""), ("added_at", "")],
    "job_skill": [("job_id", "PK FK"), ("skill_id", "PK FK"), ("importance", ""),
                  ("min_proficiency", "")],
    "application": [("application_id", "PK"), ("job_id", "FK"), ("member_id", "FK"),
                    ("source_channel", ""), ("status", ""), ("applied_at", ""),
                    ("decided_at", ""), ("resume_version", "")],
    "interview": [("interview_id", "PK"), ("application_id", "FK"), ("round_no", "UQ"),
                  ("interview_type", ""), ("scheduled_at", ""), ("duration_min", ""),
                  ("interviewer_id", "FK"), ("outcome", ""), ("score", "")],
    "referral": [("referral_id", "PK"), ("application_id", "FK UQ"), ("referrer_id", "FK"),
                 ("relationship", ""), ("referred_at", ""), ("bonus_amount", ""),
                 ("bonus_status", "")],
    "education": [("education_id", "PK"), ("member_id", "FK"), ("school_name", ""),
                  ("degree", ""), ("field_of_study", ""), ("start_year", ""), ("end_year", "")],
    "experience": [("experience_id", "PK"), ("member_id", "FK"), ("company_id", "FK"),
                   ("title", ""), ("start_date", ""), ("end_date", ""), ("is_current", ""),
                   ("current_member_id", "UQ*")],
    "connection": [("member_a_id", "PK FK"), ("member_b_id", "PK FK"), ("connected_at", ""),
                   ("connection_type", "")],
}

EDGES = [
    ("member", "application", "1", "N", "applies"),
    ("member", "interview", "1", "N", "interviews"),
    ("member", "referral", "1", "N", "refers"),
    ("company", "job_posting", "1", "N", "advertises"),
    ("company", "experience", "1", "N", "employs"),
    ("job_posting", "application", "1", "N", "receives"),
    ("job_posting", "job_skill", "1", "N", "requires"),
    ("skill", "member_skill", "1", "N", "held as"),
    ("skill", "job_skill", "1", "N", "asked as"),
    ("member", "member_skill", "1", "N", "claims"),
    ("member", "education", "1", "N", "studied"),
    ("member", "experience", "1", "N", "worked"),
    ("member", "connection", "1", "N", "connects"),
    ("application", "interview", "1", "N", "schedules"),
    ("application", "referral", "1", "1", "produced by"),
]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def seg_hits_rect(p1, p2, r, pad=6):
    x1, y1 = p1
    x2, y2 = p2
    rx, ry, rw, rh = r["x"] - pad, r["y"] - pad, r["w"] + 2 * pad, r["h"] + 2 * pad
    if abs(x1 - x2) < 0.5:
        if not (rx <= x1 <= rx + rw):
            return False
        lo, hi = sorted((y1, y2))
        return not (hi < ry or lo > ry + rh)
    if abs(y1 - y2) < 0.5:
        if not (ry <= y1 <= ry + rh):
            return False
        lo, hi = sorted((x1, x2))
        return not (hi < rx or lo > rx + rw)
    return False


def score_path(pts, boxes, skip):
    hits = 0
    length = 0
    for a, b in zip(pts, pts[1:]):
        length += abs(a[0] - b[0]) + abs(a[1] - b[1])
        for k, r in boxes.items():
            if k in skip:
                continue
            if seg_hits_rect(a, b, r):
                hits += 1
    return hits * 1000 + length


def route(s, t, boxes, back_key=None, Wc=1224):
    sx, sy = s["cx"], s["cy"]
    tx, ty = t["cx"], t["cy"]
    cands = []
    x_mid = (s["x"] + s["w"] / 2 + t["x"] + t["w"] / 2) / 2
    y1 = max(s["y"] + 16, min(t["y"] + t["h"] - 16, sy))
    y2 = max(s["y"] + 16, min(s["y"] + s["h"] - 16, ty))
    anchor_sx = s["x"] + s["w"] if tx > sx else s["x"]
    anchor_tx = t["x"] if tx > sx else t["x"] + t["w"]
    cands.append([(anchor_sx, clamp(y1, s["y"] + 14, s["y"] + s["h"] - 14)),
                  (x_mid, clamp(y1, s["y"] + 14, s["y"] + s["h"] - 14)),
                  (x_mid, clamp(y2, t["y"] + 14, t["y"] + t["h"] - 14)),
                  (anchor_tx, clamp(y2, t["y"] + 14, t["y"] + t["h"] - 14))])
    y_mid = (s["y"] + s["h"] / 2 + t["y"] + t["h"] / 2) / 2
    cands.append([(clamp(sx, s["x"] + 14, s["x"] + s["w"] - 14), s["y"] + s["h"] if ty > sy else s["y"]),
                  (clamp(sx, s["x"] + 14, s["x"] + s["w"] - 14), y_mid),
                  (clamp(tx, t["x"] + 14, t["x"] + t["w"] - 14), y_mid),
                  (clamp(tx, t["x"] + 14, t["x"] + t["w"] - 14), t["y"] if ty > sy else t["y"] + t["h"])])
    for xm in (16, Wc - 16):
        cands.append([(s["x"] if xm < 100 else s["x"] + s["w"], s["cy"]),
                      (xm, s["cy"]), (xm, t["cy"]),
                      (t["x"] if xm < 100 else t["x"] + t["w"], t["cy"])])
    # horizontal channels above and below both boxes: the only clean way past
    # a table that sits between the endpoints on the same row
    for yc in (min(s["y"], t["y"]) - 30, max(s["y"] + s["h"], t["y"] + t["h"]) + 30):
        cands.append([(sx, s["y"] if yc < s["y"] else s["y"] + s["h"]),
                      (sx, yc), (tx, yc),
                      (tx, t["y"] if yc < t["y"] else t["y"] + t["h"])])
    best = min(cands, key=lambda p: score_path(p, boxes, {back_key} if back_key else set()))
    orient = "h" if abs(best[0][1] - best[1][1]) < 0.5 else "v"
    return best, orient


def draw_table(ax, key, x, y, w):
    cols = TABLES[key]
    hh, rh = 27, 20
    h = hh + rh * len(cols) + 9
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=6",
                                linewidth=1.0, edgecolor=LGRAY, facecolor="white", zorder=2))
    ax.add_patch(FancyBboxPatch((x, y), w, hh, boxstyle="round,pad=0,rounding_size=6",
                                linewidth=0, facecolor=NAVY, zorder=3))
    ax.add_patch(Rectangle((x, y + hh - 6), w, 6, linewidth=0, facecolor=NAVY, zorder=3))
    ax.text(x + 10, y + hh / 2 + 1, key, color="white", fontsize=9.4, fontweight="bold",
            va="center", ha="left", family=FONT, zorder=4)
    for i, (col, flag) in enumerate(cols):
        ty = y + hh + 4 + i * rh
        if i % 2 == 1:
            ax.add_patch(Rectangle((x + 1, ty - 2), w - 2, rh, linewidth=0,
                                   facecolor="#F6F9FC", zorder=1))
        ax.text(x + 11, ty + rh / 2 - 2, col, fontsize=7.6, color=NAVY,
                fontweight="bold" if "PK" in flag else "normal",
                style="italic" if "FK" in flag else "normal",
                va="center", ha="left", family=FONT, zorder=5)
        if flag:
            ax.text(x + w - 9, ty + rh / 2 - 2, flag, fontsize=6.4,
                    color=BLUE if "PK" in flag else AMBER, fontweight="bold",
                    va="center", ha="right", family=FONT, zorder=5)
    return dict(key=key, x=x, y=y, w=w, h=h, cx=x + w / 2, cy=y + h / 2)


def draw_edge(ax, pts, orient):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=BLUE, lw=1.15,
            solid_capstyle="round", zorder=1.5)
    ex, ey = pts[-1]
    if orient == "h":
        d = 1 if pts[-2][0] < ex else -1
        for off in (-7, 0, 7):
            ax.plot([ex - d * 13, ex], [ey + off, ey], color=BLUE, lw=1.15, zorder=1.6)
    else:
        d = 1 if pts[-2][1] < ey else -1
        for off in (-7, 0, 7):
            ax.plot([ex + off, ex], [ey - d * 13, ey], color=BLUE, lw=1.15, zorder=1.6)


def diagram(keys, edges, out_png, title=None, cols=3, cw=352, gapx=52, gapy=84, pad=44):
    heights = [27 + 20 * len(TABLES[k]) + 9 for k in keys]
    rows = (len(keys) + cols - 1) // cols
    row_h = [max(heights[r * cols:(r + 1) * cols]) for r in range(rows)]
    Wc = pad * 2 + cols * cw + (cols - 1) * gapx
    Hc = pad * 2 + sum(row_h) + (rows - 1) * gapy + 30
    fig, ax = plt.subplots(figsize=(Wc / 100, Hc / 100), dpi=200)
    ax.set_xlim(0, Wc)
    ax.set_ylim(Hc, 0)
    ax.axis("off")
    boxes = {}
    y = pad + 26
    for r in range(rows):
        x = pad
        for c in range(cols):
            i = r * cols + c
            if i >= len(keys):
                break
            boxes[keys[i]] = draw_table(ax, keys[i], x, y, cw)
            x += cw + gapx
        y += row_h[r] + gapy
    for a, b, c1, c2, lab in edges:
        if a in boxes and b in boxes:
            pts, orient = route(boxes[a], boxes[b], boxes, b, Wc)
            draw_edge(ax, pts, orient)
    if title:
        ax.text(pad, 18, title, fontsize=10.4, color=GRAY, family=FONT, va="center")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(out_png, facecolor="white")
    fig.savefig(out_png.replace(".png", ".svg"), facecolor="white")
    plt.close(fig)
    print("wrote", os.path.basename(out_png))


# ------------------------------------------------------------------ conceptual
POS = {
    "education":     (250, 170),
    "member":        (250, 480),
    "connection":    (250, 790),
    "experience":    (250, 1090),
    "company":       (760, 1170),
    "job_posting":   (1290, 1170),
    "referral":      (1690, 210),
    "interview":     (1690, 520),
    "application":   (1690, 830),
    "skill":         (1690, 1140),
    "member_skill":  (1090, 130),
    "job_skill":     (700, 640),
}

# diamond position for each relationship.  Most sit on the midpoint of the
# line between the two entity boxes; the two marked OFF are pulled aside
# because their midpoint falls on top of a third entity.
DIAMOND_POS = {
    ("member", "education"):      (250, 325),
    ("member", "member_skill"):   (830, 238),
    ("member", "connection"):     (250, 635),
    ("member", "experience"):     (560, 1000),   # OFF: midpoint is the connection box
    ("member", "application"):    (970, 655),
    ("member", "interview"):      (970, 500),
    ("member", "referral"):       (970, 345),
    ("company", "job_posting"):   (1025, 1170),
    ("company", "experience"):    (505, 1130),
    ("job_posting", "application"): (1490, 1000),
    ("job_posting", "job_skill"): (995, 905),
    ("skill", "member_skill"):    (1510, 837),
    ("skill", "job_skill"):       (1195, 890),
    ("application", "interview"): (1690, 675),
    ("application", "referral"):  (1500, 390),   # OFF: midpoint is the interview box
}

LABELS = {(a, b): lab for a, b, c1, c2, lab in EDGES}


def conceptual(out_png):
    CW, CH = 1950, 1300
    fig, ax = plt.subplots(figsize=(CW / 130, CH / 130), dpi=200)
    ax.set_xlim(0, CW)
    ax.set_ylim(CH, 0)
    ax.axis("off")
    ax.text(40, 42, "Conceptual model - Chen notation: rectangle = entity set, diamond = relationship set, "
                    "1 / N = cardinality", fontsize=10.5, color=GRAY, family=FONT, va="center")

    ew, eh = 200, 54
    for name, (x, y) in POS.items():
        ax.add_patch(Rectangle((x - ew / 2, y - eh / 2), ew, eh, facecolor=NAVY,
                               edgecolor=NAVY, linewidth=1.2, zorder=6))
        ax.text(x, y, name, fontsize=8.8, color="white", ha="center", va="center",
                fontweight="bold", family=FONT, zorder=7)

    for a, b, c1, c2, lab in EDGES:
        if a not in POS or b not in POS:
            continue
        dx, dy = DIAMOND_POS[(a, b)]
        for end, (ex, ey) in ((a, POS[a]), (b, POS[b])):
            ax.plot([ex, dx], [ey, dy], color=LGRAY, lw=1.05, zorder=2)
        w, h = 128, 62
        ax.add_patch(Polygon([[dx, dy - h / 2], [dx + w / 2, dy], [dx, dy + h / 2],
                              [dx - w / 2, dy]], closed=True, facecolor="#E8F0F9",
                             edgecolor=BLUE, lw=1.1, zorder=4))
        ax.text(dx, dy, lab, fontsize=6.8, ha="center", va="center", color=NAVY,
                family=FONT, zorder=5)
        # cardinality next to each entity, pulled 22 px out of the diamond
        for c, (ex, ey) in ((c1, POS[a]), (c2, POS[b])):
            vx, vy = ex - dx, ey - dy
            n = max((vx * vx + vy * vy) ** 0.5, 1)
            px, py = dx + vx / n * (h / 2 + 34), dy + vy / n * (h / 2 + 34)
            ax.text(px, py, c, fontsize=8.6, color=BLUE, fontweight="bold",
                    ha="center", va="center", family=FONT, zorder=6)

    ax.text(40, CH - 26, "Attributes and keys are catalogued in design/Entity_Relationship_Catalog.md; "
                        "the logical diagram resolves every relationship set into a table.",
            fontsize=8.4, color=GRAY, family=FONT)
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(out_png, facecolor="white")
    fig.savefig(out_png.replace(".png", ".svg"), facecolor="white")
    plt.close(fig)
    print("wrote", os.path.basename(out_png))


if __name__ == "__main__":
    out = r"D:\桌面\数据库大作业\LinkedIn_交付\erd"
    os.makedirs(out, exist_ok=True)
    all_keys = list(TABLES.keys())
    diagram(all_keys, EDGES, os.path.join(out, "ERD_logical_full.png"),
            "LinkedIn hiring loop - logical schema   |   PK bold, FK italic   |   "
            "crow's foot marks the many side", cols=3, cw=372, gapx=56, gapy=92, pad=56)

    mod_a = ["member", "skill", "member_skill", "education", "experience", "connection"]
    diagram(mod_a, [e for e in EDGES if e[0] in mod_a and e[1] in mod_a],
            os.path.join(out, "ERD_module_identity.png"),
            "Module A - identity: the member, the credential record and the social graph",
            cols=3, cw=352, gapx=64, gapy=90)

    mod_b = ["company", "job_posting", "skill", "job_skill", "experience"]
    diagram(mod_b, [e for e in EDGES if e[0] in mod_b and e[1] in mod_b],
            os.path.join(out, "ERD_module_demand.png"),
            "Module B - demand: employer, posting and the skill ask", cols=3, cw=382, gapx=70, gapy=90)

    mod_c = ["job_posting", "application", "interview", "referral", "member"]
    diagram(mod_c, [e for e in EDGES if e[0] in mod_c and e[1] in mod_c],
            os.path.join(out, "ERD_module_hiring_loop.png"),
            "Module C - the hiring loop: application, interview, referral", cols=3, cw=382, gapx=70, gapy=90)

    conceptual(os.path.join(out, "ERD_conceptual.png"))
