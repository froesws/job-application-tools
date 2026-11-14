"""Renders a one-page CV PDF from master_cv.json + a "selection".

The selection only picks and orders items that already exist in the master file
(ids), so the renderer can never produce a claim that is not in your master data.
"""
import io
import json
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#1B2A41")
ACCENT = colors.HexColor("#1F5F8B")
GRAY = colors.HexColor("#4A5568")
LIGHT = colors.HexColor("#C5D3E0")
TEXT = colors.HexColor("#1F2933")

TITLES = {
    "summary": ("Summary", "Resumo"),
    "skills": ("Skills", "Competências"),
    "experience": ("Professional Experience", "Experiência Profissional"),
    "research": ("Research Experience", "Experiência de Pesquisa"),
    "projects": ("Projects", "Projetos"),
    "education": ("Education", "Educação"),
    "certs": ("Certifications & Languages", "Certificações e Idiomas"),
}

# (font scale, max bullets per role). Tried in order until the CV fits on one page.
ATTEMPTS = [(1.0, None), (0.97, None), (0.94, None), (0.94, 5), (0.94, 4), (0.94, 3)]


# ----------------------------------------------------------------------------- fonts
def setup_fonts():
    """Prefer Carlito/Calibri; fall back to built-in Helvetica (still fine for PT accents)."""
    dirs = [os.environ.get("CV_FONT_DIR", ""), "/usr/share/fonts/truetype/crosextra",
            "/usr/share/fonts/truetype/carlito", os.path.expanduser("~/.local/share/fonts"),
            "C:/Windows/Fonts", "/Library/Fonts", "/System/Library/Fonts/Supplemental"]
    names = [("Carlito-Regular.ttf", "Carlito-Bold.ttf", "Carlito-Italic.ttf", "Carlito-BoldItalic.ttf"),
             ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf")]
    for d in filter(None, dirs):
        for reg, bold, ital, bi in names:
            if all(os.path.exists(os.path.join(d, n)) for n in (reg, bold, ital, bi)):
                pdfmetrics.registerFont(TTFont("CV", os.path.join(d, reg)))
                pdfmetrics.registerFont(TTFont("CV-B", os.path.join(d, bold)))
                pdfmetrics.registerFont(TTFont("CV-I", os.path.join(d, ital)))
                pdfmetrics.registerFont(TTFont("CV-BI", os.path.join(d, bi)))
                pdfmetrics.registerFontFamily("CV", normal="CV", bold="CV-B", italic="CV-I", boldItalic="CV-BI")
                return {"r": "CV", "b": "CV-B", "i": "CV-I", "bi": "CV-BI"}
    return {"r": "Helvetica", "b": "Helvetica-Bold", "i": "Helvetica-Oblique", "bi": "Helvetica-BoldOblique"}


# ----------------------------------------------------------------------------- data helpers
def load_master(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tr(obj, key, lang):
    return obj.get(f"{key}_{lang}", "")


def item_text(item, lang):
    return item if isinstance(item, str) else item[lang]


def item_keys(item):
    return {item.lower()} if isinstance(item, str) else {item["en"].lower(), item["pt"].lower()}


def _roles(master):
    return {r["id"]: r for e in master["experience"] for r in e["roles"]}


def _research(master):
    return {r["id"]: r for r in master["research"]}


# ----------------------------------------------------------------------------- validation
def validate_selection(master, sel):
    """Return a list of problems. Empty list = the selection is safe to render."""
    errs = []
    if sel.get("language") not in ("en", "pt"):
        errs.append("language must be 'en' or 'pt'")
    if sel.get("role_id") not in {r["id"] for r in master["role_options"]}:
        errs.append(f"role_id unknown: {sel.get('role_id')}")

    blocks = {b["id"]: b for b in master["summary_blocks"]}
    ids = sel.get("summary_ids", [])
    if not 1 <= len(ids) <= 4:
        errs.append("summary_ids must have 1 to 4 ids")
    for i in ids:
        if i not in blocks:
            errs.append(f"summary id unknown: {i}")
    if ids and ids[0] in blocks and not blocks[ids[0]].get("lead"):
        errs.append("the first summary id must be a 'lead' block")

    for kind, catalog in (("experience", _roles(master)), ("research", _research(master))):
        for key, bullet_ids in sel.get(kind, {}).items():
            if key not in catalog:
                errs.append(f"{kind} id unknown: {key}")
                continue
            valid = {b["id"] for b in catalog[key]["bullets"]}
            if len(set(bullet_ids)) != len(bullet_ids):
                errs.append(f"{kind}/{key}: duplicate bullet ids")
            if not 1 <= len(bullet_ids) <= 7:
                errs.append(f"{kind}/{key}: needs 1 to 7 bullets")
            for b in bullet_ids:
                if b not in valid:
                    errs.append(f"{kind}/{key}: bullet id not in master: {b}")

    valid_projects = {p["id"] for p in master["projects"]}
    for p in sel.get("project_ids", []):
        if p not in valid_projects:
            errs.append(f"project id unknown: {p}")

    known = set()
    for g in master["skills"]:
        for it in g["core"] + g["extra"]:
            known |= item_keys(it)
    for s in sel.get("skill_priority", []):
        if s.lower() not in known:
            errs.append(f"skill not in master: {s}")
    return errs


# ----------------------------------------------------------------------------- layout
def _styles(f, k):
    def ps(name, **kw):
        return ParagraphStyle(name, **kw)
    return {
        "name": ps("name", fontName=f["b"], fontSize=25, leading=29, alignment=TA_CENTER, textColor=NAVY),
        "role": ps("role", fontName=f["b"], fontSize=12, leading=15, alignment=TA_CENTER, textColor=ACCENT),
        "contact": ps("contact", fontName=f["r"], fontSize=9.6, leading=12.5, alignment=TA_CENTER, textColor=GRAY),
        "links": ps("links", fontName=f["r"], fontSize=9.6, leading=12.5, alignment=TA_CENTER, textColor=ACCENT),
        "h": ps("h", fontName=f["b"], fontSize=10, leading=12, textColor=ACCENT, charSpace=1.1),
        "p": ps("p", fontName=f["r"], fontSize=9.4 * k, leading=11.6 * k, textColor=TEXT, alignment=TA_LEFT),
        "skill": ps("skill", fontName=f["r"], fontSize=9.4 * k, leading=11.6 * k, textColor=TEXT, spaceAfter=1.5),
        "b": ps("b", fontName=f["r"], fontSize=9.4 * k, leading=11.4 * k, textColor=TEXT,
                leftIndent=10, bulletIndent=1, spaceAfter=1.2),
        "jl": ps("jl", fontName=f["b"], fontSize=10.3 * k, leading=12.5 * k, textColor=NAVY),
        "jr": ps("jr", fontName=f["r"], fontSize=9.4 * k, leading=12.5 * k, textColor=GRAY, alignment=TA_RIGHT),
        "sl": ps("sl", fontName=f["bi"], fontSize=9.7 * k, leading=12 * k, textColor=TEXT),
        "sr": ps("sr", fontName=f["i"], fontSize=9.3 * k, leading=12 * k, textColor=GRAY, alignment=TA_RIGHT),
    }


def _build_story(master, sel, lang, k, cap, f, cw):
    S = _styles(f, k)
    pers = master["person"]
    story = []

    def heading(key):
        story.extend([Spacer(1, 3), Paragraph(esc(TITLES[key][0 if lang == "en" else 1].upper()), S["h"]),
                      HRFlowable(width="100%", thickness=0.7, color=LIGHT, spaceBefore=1.5, spaceAfter=3)])

    def row(left, right, ls, rs):
        t = Table([[Paragraph(esc(left), S[ls]), Paragraph(esc(right), S[rs])]],
                  colWidths=[(cw - 12) * 0.76, (cw - 12) * 0.24], hAlign="LEFT")
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
        return t

    def bullets(items):
        return [Paragraph(esc(i), S["b"], bulletText="\u2022") for i in items]

    # header
    role = next(r for r in master["role_options"] if r["id"] == sel["role_id"])
    phone = pers["phone_intl"] if lang == "en" else pers["phone_local"]
    sep = "\u00a0\u00a0\u00b7\u00a0\u00a0"
    story.append(Paragraph(esc(pers["name"]), S["name"]))
    story.append(Paragraph(esc(role[lang]), S["role"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f'{esc(phone)}{sep}<a href="mailto:{pers["email"]}">{esc(pers["email"])}</a>', S["contact"]))
    story.append(Paragraph(esc(tr(pers, "location", lang).replace(" \u00b7 ", sep)), S["contact"]))
    story.append(Spacer(1, 3))
    story.append(Paragraph(sep.join(f'<a href="{l["url"]}">{esc(l["label"])}</a>' for l in pers["links"]), S["links"]))
    story.append(Spacer(1, 5))
    story.append(HRFlowable(width="100%", thickness=1.2, color=NAVY, spaceBefore=0, spaceAfter=2))

    # summary
    blocks = {b["id"]: b for b in master["summary_blocks"]}
    heading("summary")
    story.append(Paragraph(esc(" ".join(blocks[i][lang] for i in sel["summary_ids"])), S["p"]))

    # skills: core items, plus extras the job asks for; priority terms first
    prio = [s.lower() for s in sel.get("skill_priority", [])]
    heading("skills")
    for g in master["skills"]:
        items = list(g["core"]) + [it for it in g["extra"] if item_keys(it) & set(prio)]

        def rank(it):
            hit = [i for i, p in enumerate(prio) if p in item_keys(it)]
            return (0, hit[0]) if hit else (1, 0)
        items = sorted(items, key=rank)  # stable: non-priority items keep master order
        story.append(Paragraph(f"<b>{esc(tr(g, 'label', lang))}</b> {esc(', '.join(item_text(i, lang) for i in items))}", S["skill"]))

    # experience
    heading("experience")
    for e in master["experience"]:
        story.append(row(tr(e, "header", lang), tr(e, "date", lang), "jl", "jr"))
        for r in e["roles"]:
            order = sel.get("experience", {}).get(r["id"]) or [b["id"] for b in r["bullets"]]
            if cap:
                order = order[:cap]
            by_id = {b["id"]: b for b in r["bullets"]}
            story.append(Spacer(1, 2))
            story.append(row(tr(r, "title", lang), tr(r, "date", lang), "sl", "sr"))
            story.append(Paragraph(esc(tr(r, "intro", lang)), S["p"]))
            story.append(Spacer(1, 2))
            story.extend(bullets([by_id[i][lang] for i in order]))

    # research
    heading("research")
    research = _research(master)
    for n, rid in enumerate(sel.get("research_ids") or list(research)):
        r = research[rid]
        order = sel.get("research", {}).get(rid) or [b["id"] for b in r["bullets"]]
        if cap:
            order = order[:cap]
        by_id = {b["id"]: b for b in r["bullets"]}
        if n:
            story.append(Spacer(1, 2))
        story.append(row(tr(r, "header", lang), tr(r, "date", lang), "jl", "jr"))
        if tr(r, "intro", lang):
            story.append(Paragraph(esc(tr(r, "intro", lang)), S["p"]))
        story.append(Spacer(1, 2))
        story.extend(bullets([by_id[i][lang] for i in order]))

    # projects
    projects = {p["id"]: p for p in master["projects"]}
    chosen = sel.get("project_ids", [])
    if chosen:
        heading("projects")
        story.extend(bullets([projects[i][lang] for i in chosen]))

    # education
    heading("education")
    for n, ed in enumerate(master["education"]):
        if n:
            story.append(Spacer(1, 2))
        story.append(row(tr(ed, "header", lang), ed["date"], "jl", "jr"))
        if tr(ed, "desc", lang):
            story.append(Paragraph(esc(tr(ed, "desc", lang)), S["p"]))

    heading("certs")
    story.append(Paragraph(esc(master["certs"][lang].replace(" \u00b7 ", sep)), S["p"]))
    return story


def render_pdf(master, sel, out_path):
    """Render to out_path, shrinking spacing / trimming bullets until it fits on one page."""
    errs = validate_selection(master, sel)
    if errs:
        raise ValueError("Invalid selection:\n- " + "\n- ".join(errs))
    lang = sel["language"]
    f = setup_fonts()
    lm = rm = 14.5 * mm
    cw = A4[0] - lm - rm
    last = None
    for k, cap in ATTEMPTS:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=lm, rightMargin=rm, topMargin=9 * mm,
                                bottomMargin=8 * mm, title=f"{master['person']['name']} - CV",
                                author=master["person"]["name"])
        doc.build(_build_story(master, sel, lang, k, cap, f, cw))
        last = (buf.getvalue(), doc.page, k, cap)
        if doc.page == 1:
            break
    data, pages, k, cap = last
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_bytes(data)
    return {"pages": pages, "font_scale": k, "bullet_cap": cap, "font": f["r"], "path": str(out_path)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Render a CV PDF from a selection JSON")
    ap.add_argument("selection")
    ap.add_argument("--master", default=str(Path(__file__).resolve().parents[4] / "profile" / "master.json"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print(render_pdf(load_master(a.master), json.loads(Path(a.selection).read_text(encoding="utf-8")), a.out))
