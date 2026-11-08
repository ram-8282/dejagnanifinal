#!/usr/bin/env python3
"""
Modify the Déjà pitching slides by rewriting each slide's text boxes
to match the actual project content. Uses defusedxml.minidom for safe
round-tripping so namespace prefixes are preserved.
"""

import os
import re
import zipfile
import shutil
import defusedxml.minidom as dm
from xml.dom.minidom import parseString, Document

SRC = "Pitching Slides.pptx"
OUT = "Deja_Pitching_Slides.pptx"
UNPACK = "unpacked"

# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------
NS = {
    "a":  "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p":  "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r":  "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

def emu(inches):
    return int(inches * 914400)

def read_xml(path):
    with open(path, "rb") as f:
        raw = f.read()
    return dm.parseString(raw)

def write_xml(doc, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc.toxml())

def tag(ns_prefix, local):
    return f"{{{NS[ns_prefix]}}}{local}"

# ---------------------------------------------------------------------------
# Low-level node builders  (work on any xml.dom.minidom Document)
# ---------------------------------------------------------------------------

def _a(doc, local, **attrs):
    el = doc.createElementNS(NS["a"], f"a:{local}")
    for k, v in attrs.items():
        el.setAttribute(k, str(v))
    return el

def _p(doc, local, **attrs):
    el = doc.createElementNS(NS["p"], f"p:{local}")
    for k, v in attrs.items():
        el.setAttribute(k, str(v))
    return el

def make_run(doc, text, sz=1400, bold=False, color=None, face="Calibri"):
    """Return a <a:r> node."""
    r = _a(doc, "r")
    rPr = _a(doc, "rPr", lang="en-US", sz=str(sz), dirty="0")
    if bold:
        rPr.setAttribute("b", "1")
    if color:
        fill = _a(doc, "solidFill")
        clr  = _a(doc, "srgbClr", val=color)
        fill.appendChild(clr)
        rPr.appendChild(fill)
    lat = _a(doc, "latin", typeface=face, pitchFamily="2", charset="0")
    rPr.appendChild(lat)
    r.appendChild(rPr)
    t = doc.createElementNS(NS["a"], "a:t")
    t.appendChild(doc.createTextNode(text))
    r.appendChild(t)
    return r

def make_para(doc, runs_or_text, align="l", space_before=None, bullet=False, sz=1400, bold=False, color=None, face="Calibri"):
    """Return a <a:p> with one or more runs."""
    p = _a(doc, "p")
    pPr = _a(doc, "pPr")
    if align != "l":
        pPr.setAttribute("algn", align)
    if space_before:
        spc = _a(doc, "spcBef")
        spcPts = _a(doc, "spcPts", val=str(space_before))
        spc.appendChild(spcPts)
        pPr.appendChild(spc)
    if bullet:
        buFont = _a(doc, "buFont", typeface="Arial", pitchFamily="34", charset="0")
        buChar = _a(doc, "buChar")
        buChar.setAttribute("char", "•")
        pPr.appendChild(buFont)
        pPr.appendChild(buChar)
    p.appendChild(pPr)
    if isinstance(runs_or_text, str):
        p.appendChild(make_run(doc, runs_or_text, sz=sz, bold=bold, color=color, face=face))
    else:
        for r in runs_or_text:
            p.appendChild(r)
    endPr = _a(doc, "endParaRPr", lang="en-US", dirty="0")
    p.appendChild(endPr)
    return p

def make_textbox(doc, x, y, cx, cy, paras, valign="t", wrap=True):
    """
    Return a <p:sp> textbox (no placeholder).
    paras: list of <a:p> nodes
    """
    sp = _p(doc, "sp")
    nvSpPr = _p(doc, "nvSpPr")
    cNvPr  = _p(doc, "cNvPr", id="99", name="TextBox")
    cNvSpPr = _p(doc, "cNvSpPr", txBox="1")
    spLocks = _a(doc, "spLocks", noGrp="1")
    cNvSpPr.appendChild(spLocks)
    nvPr = _p(doc, "nvPr")
    nvSpPr.appendChild(cNvPr)
    nvSpPr.appendChild(cNvSpPr)
    nvSpPr.appendChild(nvPr)
    sp.appendChild(nvSpPr)

    spPr = _p(doc, "spPr")
    xfrm = _a(doc, "xfrm")
    off  = _a(doc, "off", x=str(x), y=str(y))
    ext  = _a(doc, "ext", cx=str(cx), cy=str(cy))
    xfrm.appendChild(off)
    xfrm.appendChild(ext)
    prstGeom = _a(doc, "prstGeom", prst="rect")
    prstGeom.appendChild(_a(doc, "avLst"))
    noFill = _a(doc, "noFill")
    spPr.appendChild(xfrm)
    spPr.appendChild(prstGeom)
    spPr.appendChild(noFill)
    sp.appendChild(spPr)

    txBody = _p(doc, "txBody")
    bodyPr = _a(doc, "bodyPr", wrap="square" if wrap else "none",
                lIns="91440", tIns="45720", rIns="91440", bIns="45720",
                anchor=valign)
    bodyPr.appendChild(_a(doc, "spAutoFit"))
    lstStyle = _a(doc, "lstStyle")
    txBody.appendChild(bodyPr)
    txBody.appendChild(lstStyle)
    for p in paras:
        txBody.appendChild(p)
    sp.appendChild(txBody)
    return sp

def make_rect(doc, x, y, cx, cy, fill_color, line_color=None, line_w=None, rounded=False):
    """Return a <p:sp> filled rectangle."""
    sp = _p(doc, "sp")
    nvSpPr = _p(doc, "nvSpPr")
    cNvPr  = _p(doc, "cNvPr", id="88", name="Rect")
    cNvSpPr = _p(doc, "cNvSpPr")
    nvPr   = _p(doc, "nvPr")
    nvSpPr.appendChild(cNvPr)
    nvSpPr.appendChild(cNvSpPr)
    nvSpPr.appendChild(nvPr)
    sp.appendChild(nvSpPr)

    spPr = _p(doc, "spPr")
    xfrm = _a(doc, "xfrm")
    xfrm.appendChild(_a(doc, "off", x=str(x), y=str(y)))
    xfrm.appendChild(_a(doc, "ext", cx=str(cx), cy=str(cy)))
    prst = "roundRect" if rounded else "rect"
    prstGeom = _a(doc, "prstGeom", prst=prst)
    if rounded:
        avLst = _a(doc, "avLst")
        gd = _a(doc, "gd", name="adj", fmla="val 16667")
        avLst.appendChild(gd)
        prstGeom.appendChild(avLst)
    else:
        prstGeom.appendChild(_a(doc, "avLst"))
    solidFill = _a(doc, "solidFill")
    solidFill.appendChild(_a(doc, "srgbClr", val=fill_color))
    spPr.appendChild(xfrm)
    spPr.appendChild(prstGeom)
    spPr.appendChild(solidFill)
    if line_color:
        ln = _a(doc, "ln", w=str(line_w or 9525))
        lnFill = _a(doc, "solidFill")
        lnFill.appendChild(_a(doc, "srgbClr", val=line_color))
        ln.appendChild(lnFill)
        spPr.appendChild(ln)
    else:
        ln = _a(doc, "ln")
        ln.appendChild(_a(doc, "noFill"))
        spPr.appendChild(ln)
    sp.appendChild(spPr)
    txBody = _p(doc, "txBody")
    txBody.appendChild(_a(doc, "bodyPr"))
    txBody.appendChild(_a(doc, "lstStyle"))
    txBody.appendChild(_a(doc, "p"))   # required empty paragraph
    sp.appendChild(txBody)
    return sp

def make_line(doc, x1, y1, x2, y2, color="C00000", w=19050):
    """Return a <p:sp> connector line."""
    sp = _p(doc, "sp")
    nvSpPr = _p(doc, "nvSpPr")
    nvSpPr.appendChild(_p(doc, "cNvPr", id="77", name="Line"))
    nvSpPr.appendChild(_p(doc, "cNvSpPr"))
    nvSpPr.appendChild(_p(doc, "nvPr"))
    sp.appendChild(nvSpPr)
    spPr = _p(doc, "spPr")
    cx = x2 - x1
    cy = y2 - y1
    xfrm = _a(doc, "xfrm")
    xfrm.appendChild(_a(doc, "off", x=str(min(x1,x2)), y=str(min(y1,y2))))
    xfrm.appendChild(_a(doc, "ext", cx=str(abs(cx)), cy=str(abs(cy))))
    prstGeom = _a(doc, "prstGeom", prst="line")
    prstGeom.appendChild(_a(doc, "avLst"))
    noFill = _a(doc, "noFill")
    ln = _a(doc, "ln", w=str(w))
    solidFill = _a(doc, "solidFill")
    solidFill.appendChild(_a(doc, "srgbClr", val=color))
    ln.appendChild(solidFill)
    spPr.appendChild(xfrm)
    spPr.appendChild(prstGeom)
    spPr.appendChild(noFill)
    spPr.appendChild(ln)
    sp.appendChild(spPr)
    txBody = _p(doc, "txBody")
    txBody.appendChild(_a(doc, "bodyPr"))
    txBody.appendChild(_a(doc, "lstStyle"))
    txBody.appendChild(_a(doc, "p"))   # required empty paragraph
    sp.appendChild(txBody)
    return sp


def clear_spTree(doc):
    """Return a fresh <p:spTree> with just the required group header plus
    invisible placeholder overrides to suppress layout body/title inheritance."""
    spTree = _p(doc, "spTree")
    nvGrpSpPr = _p(doc, "nvGrpSpPr")
    nvGrpSpPr.appendChild(_p(doc, "cNvPr", id="1", name=""))
    nvGrpSpPr.appendChild(_p(doc, "cNvGrpSpPr"))
    nvGrpSpPr.appendChild(_p(doc, "nvPr"))
    grpSpPr = _p(doc, "grpSpPr")
    xfrm = _a(doc, "xfrm")
    xfrm.appendChild(_a(doc, "off", x="0", y="0"))
    xfrm.appendChild(_a(doc, "ext", cx="0", cy="0"))
    xfrm.appendChild(_a(doc, "chOff", x="0", y="0"))
    xfrm.appendChild(_a(doc, "chExt", cx="0", cy="0"))
    grpSpPr.appendChild(xfrm)
    spTree.appendChild(nvGrpSpPr)
    spTree.appendChild(grpSpPr)

    # Add invisible placeholder overrides for title and body so the layout's
    # "Click to edit..." placeholder text doesn't bleed through.
    for ph_type, ph_idx, sp_id in [("title", None, "2"), ("", "1", "3")]:
        sp = _p(doc, "sp")
        nvSpPr = _p(doc, "nvSpPr")
        cNvPr = _p(doc, "cNvPr", id=sp_id, name=f"ph_{sp_id}")
        cNvSpPr = _p(doc, "cNvSpPr")
        spLocks = _a(doc, "spLocks", noGrp="1")
        cNvSpPr.appendChild(spLocks)
        nvPr = _p(doc, "nvPr")
        ph = _p(doc, "ph")
        if ph_type:
            ph.setAttribute("type", ph_type)
        if ph_idx is not None:
            ph.setAttribute("idx", ph_idx)
        nvPr.appendChild(ph)
        nvSpPr.appendChild(cNvPr)
        nvSpPr.appendChild(cNvSpPr)
        nvSpPr.appendChild(nvPr)
        sp.appendChild(nvSpPr)
        spPr = _p(doc, "spPr")
        # Position off-slide so it's invisible (x=-W, y=-H)
        xfrm2 = _a(doc, "xfrm")
        xfrm2.appendChild(_a(doc, "off", x="-9144000", y="-5143500"))
        xfrm2.appendChild(_a(doc, "ext", cx="100", cy="100"))
        spPr.appendChild(xfrm2)
        sp.appendChild(spPr)
        txBody = _p(doc, "txBody")
        txBody.appendChild(_a(doc, "bodyPr"))
        txBody.appendChild(_a(doc, "lstStyle"))
        txBody.appendChild(_a(doc, "p"))
        sp.appendChild(txBody)
        spTree.appendChild(sp)

    return spTree


def replace_spTree(slide_doc, new_spTree):
    """Replace the <p:spTree> inside the slide's <p:cSld> and suppress
    layout/master placeholders so they don't bleed through."""
    cSld = slide_doc.getElementsByTagNameNS(NS["p"], "cSld")[0]
    # Suppress inherited master/layout shapes
    cSld.setAttribute("showMasterSp", "0")
    old  = cSld.getElementsByTagNameNS(NS["p"], "spTree")[0]
    cSld.replaceChild(new_spTree, old)


# ---------------------------------------------------------------------------
# Palette — Midnight Executive (navy / ice-blue / amber)
# ---------------------------------------------------------------------------
NAVY    = "002060"
ICE     = "CADCFC"
AMBER   = "FFC000"
WHITE   = "FFFFFF"
LGRAY   = "D9D9D9"
DKGRAY  = "595959"
MID     = "1C4587"   # mid-navy for cards
TEAL    = "028090"
MINT    = "02C39A"
CORAL   = "C00000"

W  = 9144000   # slide width EMU
H  = 5143500   # slide height EMU
M  = 457200    # 0.5" margin

# ---------------------------------------------------------------------------
# Slide builders
# ---------------------------------------------------------------------------

def build_slide_header(doc, spTree, title_text, subtitle=None):
    """Dark navy header bar at top with white title, optional subtitle below."""
    # Full white background behind content area (masks any layout placeholder bleed-through)
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    # Header bar
    spTree.appendChild(make_rect(doc, 0, 0, W, emu(1.15), NAVY))
    # Title
    title_paras = [make_para(doc, title_text, align="l", sz=3200, bold=True, color=WHITE, face="Cambria")]
    spTree.appendChild(make_textbox(doc, M, emu(0.1), W - 2*M, emu(0.95),
                                    title_paras, valign="ctr"))
    # Amber accent dot
    spTree.appendChild(make_rect(doc, W - emu(0.35), emu(0.42), emu(0.18), emu(0.18), AMBER, rounded=True))
    if subtitle:
        sub_paras = [make_para(doc, subtitle, align="l", sz=1100, color=DKGRAY, face="Calibri")]
        spTree.appendChild(make_textbox(doc, M, emu(1.18), W - 2*M, emu(0.32), sub_paras, valign="ctr"))


def build_card(doc, spTree, x, y, cx, cy, header, bullets, hdr_color=MID, txt_color="212121"):
    """Rounded card with colored header block and bullet content."""
    # Card background
    spTree.appendChild(make_rect(doc, x, y, cx, cy, "F0F4FA", line_color="C5D5EA", line_w=9525))
    # Header strip
    spTree.appendChild(make_rect(doc, x, y, cx, emu(0.38), hdr_color))
    hdr_paras = [make_para(doc, header, align="l", sz=1400, bold=True, color=WHITE, face="Calibri")]
    spTree.appendChild(make_textbox(doc, x + emu(0.12), y + emu(0.04), cx - emu(0.24), emu(0.30),
                                    hdr_paras, valign="ctr"))
    # Bullets
    bullet_paras = []
    for b in bullets:
        bullet_paras.append(make_para(doc, b, bullet=True, sz=1200, color=txt_color, face="Calibri"))
    spTree.appendChild(make_textbox(doc, x + emu(0.12), y + emu(0.44), cx - emu(0.24), cy - emu(0.54),
                                    bullet_paras))

def build_stat_box(doc, spTree, x, y, cx, cy, number, label, bg=MID):
    """Big stat callout box."""
    spTree.appendChild(make_rect(doc, x, y, cx, cy, bg, line_color="CADCFC", line_w=9525))
    # Handle multi-line number (e.g. "top_k\n=150")
    num_lines = number.split("\n")
    num_h = emu(0.6) if len(num_lines) > 1 else emu(0.55)
    num_sz = 2600 if len(num_lines) > 1 else 3200
    num_paras = [make_para(doc, l, align="ctr", sz=num_sz, bold=True, color=WHITE, face="Cambria") for l in num_lines]
    spTree.appendChild(make_textbox(doc, x + emu(0.05), y + emu(0.06), cx - emu(0.1), num_h, num_paras, valign="ctr"))
    lbl_lines = label.split("\n")
    lbl_paras = [make_para(doc, l, align="ctr", sz=1000, color=ICE, face="Calibri") for l in lbl_lines]
    spTree.appendChild(make_textbox(doc, x + emu(0.05), y + num_h + emu(0.12), cx - emu(0.1), cy - num_h - emu(0.18), lbl_paras))




# ---------------------------------------------------------------------------
# SLIDE 1 — Title / Cover
# ---------------------------------------------------------------------------
def build_slide1(doc):
    spTree = clear_spTree(doc)
    # Full background
    spTree.appendChild(make_rect(doc, 0, 0, W, H, NAVY))
    # Diagonal accent shape (top-right quadrant teal strip)
    spTree.appendChild(make_rect(doc, W - emu(2.5), 0, emu(2.5), emu(1.8), MID))
    # Amber bar at bottom
    spTree.appendChild(make_rect(doc, 0, H - emu(0.25), W, emu(0.25), AMBER))

    # Main title
    title_paras = [
        make_para(doc, "Déjà", align="l", sz=6000, bold=True, color=WHITE, face="Cambria"),
    ]
    spTree.appendChild(make_textbox(doc, M, emu(0.8), emu(5.5), emu(1.2), title_paras))

    # Tagline
    tag_paras = [make_para(doc, "Cognee-Powered Personal Memory Recovery Engine", align="l",
                            sz=1800, color=ICE, face="Calibri")]
    spTree.appendChild(make_textbox(doc, M, emu(2.1), emu(6.0), emu(0.5), tag_paras))

    # Sub-tag
    subtag = [make_para(doc, "Build your external brain. Query your past. Recover the forgotten.", align="l",
                         sz=1300, color=AMBER, face="Calibri")]
    spTree.appendChild(make_textbox(doc, M, emu(2.65), emu(6.0), emu(0.4), subtag))

    # Event / college info box
    spTree.appendChild(make_rect(doc, M, emu(3.4), emu(5.5), emu(1.3), MID))
    info = [
        make_para(doc, "CMR THINKFEST 3.0  •  01st August 2026", align="l", sz=1300, bold=True, color=WHITE, face="Calibri"),
        make_para(doc, "CMR College of Engineering & Technology, Hyderabad", align="l", sz=1100, color=ICE, face="Calibri"),
    ]
    spTree.appendChild(make_textbox(doc, M + emu(0.15), emu(3.52), emu(5.2), emu(1.0), info))

    # SDG tag
    sdg = [make_para(doc, "SDG 3: Good Health & Well-Being  |  SDG 9: Industry, Innovation & Infrastructure",
                      align="l", sz=1000, color=AMBER, face="Calibri")]
    spTree.appendChild(make_textbox(doc, M, emu(4.75), W - 2*M, emu(0.3), sdg))

    replace_spTree(doc, spTree)


# ---------------------------------------------------------------------------
# SLIDE 2 — Problem Statement
# ---------------------------------------------------------------------------
def build_slide2(doc):
    spTree = clear_spTree(doc)
    # White bg
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    build_slide_header(doc, spTree, "PROBLEM STATEMENT", "The crisis of cognitive overload in modern life")

    # Problem statement big quote
    spTree.appendChild(make_rect(doc, M, emu(1.35), W - 2*M, emu(0.6), ICE))
    quote = [make_para(doc, "\"Humans forget ~70% of new information within 24 hours — and there is no search engine for your own mind.\"",
                        align="ctr", sz=1400, bold=False, color=NAVY, face="Cambria")]
    spTree.appendChild(make_textbox(doc, M + emu(0.15), emu(1.42), W - 2*M - emu(0.3), emu(0.5), quote, valign="ctr"))

    # Two-column problem + solution
    col_w = emu(4.0)
    col_h = emu(2.5)
    gap   = emu(0.2)
    col1_x = M
    col2_x = M + col_w + gap

    build_card(doc, spTree, col1_x, emu(2.05), col_w, col_h,
               "THE PROBLEM",
               [
                   "No personal semantic memory layer for individuals",
                   "Journals and notes lack intelligent cross-referencing",
                   "Forgotten habits, contradictions & patterns stay invisible",
                   "Existing AI tools have no personalized longitudinal context",
               ], hdr_color=CORAL)

    build_card(doc, spTree, col2_x, emu(2.05), col_w, col_h,
               "OUR SOLUTION — DÉJÀ",
               [
                   "Semantic knowledge graph built from your own journal entries",
                   "Natural-language Q&A over your entire personal history",
                   "Automated contradiction & gap detection (Blindspots)",
                   "Dual local + cloud architecture — private & scalable",
               ], hdr_color=MID)

    replace_spTree(doc, spTree)


# ---------------------------------------------------------------------------
# SLIDE 3 — Customer Segments
# ---------------------------------------------------------------------------
def build_slide3(doc):
    spTree = clear_spTree(doc)
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    build_slide_header(doc, spTree, "1. CUSTOMER SEGMENTS", "Who are we creating value for?")

    # Three audience cards
    cards = [
        (TEAL, "Students & Job Seekers",
         ["Track study habits, mood-performance links",
          "Recall preparation timelines for exams/interviews",
          "Identify study pattern gaps before deadlines"]),
        (MID, "Knowledge Workers & Researchers",
         ["Journal-based project memory for long-term work",
          "Semantic retrieval across months of notes & ideas",
          "Contradiction detection in research hypotheses"]),
        (CORAL, "Mental Wellness & Self-Improvement",
         ["Habit tracking with intelligent pattern analysis",
          "Reflect on behavioural trends over months & years",
          "Privacy-first local or cloud graph storage"]),
    ]
    card_w = emu(2.75)
    card_h = emu(3.0)
    gap    = emu(0.16)
    total  = 3 * card_w + 2 * gap
    start_x = (W - total) // 2

    for i, (color, title, bullets) in enumerate(cards):
        cx = start_x + i * (card_w + gap)
        build_card(doc, spTree, cx, emu(1.4), card_w, card_h, title, bullets, hdr_color=color)

    # Bottom tagline
    tagline = [make_para(doc, "Primary Market: Tech-savvy individuals aged 18-35 who journal digitally and value AI-augmented self-awareness.",
                          align="ctr", sz=1100, color=DKGRAY, face="Calibri")]
    spTree.appendChild(make_textbox(doc, M, emu(4.55), W - 2*M, emu(0.4), tagline))

    replace_spTree(doc, spTree)


def build_slide4(doc):
    spTree = clear_spTree(doc)
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    build_slide_header(doc, spTree, "2. UNIQUE VALUE PROPOSITION (UVP)", "Why Déjà stands out as the ultimate cognitive companion")

    # 4 columns for UVPs
    uvps = [
        (TEAL, "Dynamic Hybrid Indexing",
         ["Bridges time-series timelines (Supabase) with semantic graph networks (Cognee).",
          "Maintains absolute chronological accuracy while enabling deep concept relationships.",
          "Constructs a living external brain layer of experiences."]),
        (MID, "Paradox & Gap Detection",
         ["Our proprietary Blindspots Engine compares memory graph density with timeline logs.",
          "Automatically detects abandoned habits, routine shifts, and semantic contradictions.",
          "Surfaces insights you forgot to remember."]),
        (CORAL, "Memory Sanctuary",
         ["Provides target node & edge pruning in the vector space via cognee.forget().",
          "True GDPR-aligned 'right to be forgotten' at a conceptual level.",
          "Users choose what the AI retains, remembers, or permanently dissolves."]),
        (AMBER, "10× Accelerated Recall",
         ["Custom hybrid query pipeline cuts semantic retrieval latency down to ~1.5s.",
          "Bypasses standard slow LLM graph traversals for instant response times.",
          "Maintains dense context lookup (top_k=150) under peak load."]),
    ]

    col_w = emu(1.95)
    col_h = emu(3.18)
    gap = emu(0.16)
    total = 4 * col_w + 3 * gap
    sx = (W - total) // 2

    for i, (color, title, bullets) in enumerate(uvps):
        cx = sx + i * (col_w + gap)
        cy = emu(1.52)
        build_card(doc, spTree, cx, cy, col_w, col_h, title, bullets, hdr_color=color)

    replace_spTree(doc, spTree)



# ---------------------------------------------------------------------------
# SLIDE 5 — Key Activities / System Architecture
# ---------------------------------------------------------------------------
def build_slide5(doc):
    spTree = clear_spTree(doc)
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    build_slide_header(doc, spTree, "SYSTEM ARCHITECTURE & KEY ACTIVITIES",
                        "5-layer hybrid stack: React → Express → FastAPI → Cognee → SQLite/LanceDB")

    # Architecture flow diagram — 5 boxes connected by arrows
    boxes = [
        (ICE,   NAVY,   "React + Vite\nFrontend",      "Glassmorphism UI\nJournal · Oracle · Blindspots"),
        (ICE,   NAVY,   "Node.js Express\nGateway :5051","API routing · Auth\nMulti-tenancy · Supabase"),
        (AMBER, NAVY,   "Python FastAPI\nBridge :8000", "Cognee SDK\nAsync queue · Embedding"),
        (MID,   WHITE,  "Cognee OS\nLocal Mode",        "SQLite + LanceDB\nPrivate / offline"),
        (TEAL,  WHITE,  "Cognee Cloud\nHosted Mode",    "Enterprise scale\nAuth0 device flow"),
    ]

    box_w = emu(1.55)
    box_h = emu(1.6)
    gap   = emu(0.23)
    total = len(boxes) * box_w + (len(boxes) - 1) * gap
    sx    = (W - total) // 2
    by    = emu(1.5)

    for i, (bg, txt, title, sub) in enumerate(boxes):
        bx = sx + i * (box_w + gap)
        spTree.appendChild(make_rect(doc, bx, by, box_w, box_h, bg, line_color="AAAAAA", line_w=9525))
        t_paras = [
            make_para(doc, title, align="ctr", sz=1200, bold=True, color=txt, face="Cambria"),
            make_para(doc, sub,   align="ctr", sz=1000, color=txt, face="Calibri"),
        ]
        spTree.appendChild(make_textbox(doc, bx, by + emu(0.2), box_w, box_h - emu(0.25), t_paras, valign="ctr"))
        # Arrow between boxes
        if i < len(boxes) - 1:
            ax = bx + box_w
            ay = by + box_h // 2
            spTree.appendChild(make_rect(doc, ax, ay - emu(0.04), gap, emu(0.08), AMBER))

    # Key API calls row
    api_y = emu(3.3)
    apis  = [
        ("cognee.add()", "Structured text\ningestion"),
        ("cognee.cognify()", "Builds semantic\nknowledge graph"),
        ("cognee.recall()", "Semantic graph\nretrieval"),
        ("cognee.forget()", "Memory pruning\n& graph wipe"),
    ]
    api_w = emu(2.0)
    api_h = emu(1.45)
    api_gap = emu(0.18)
    api_total = len(apis) * api_w + (len(apis)-1)*api_gap
    api_sx = (W - api_total) // 2

    label = [make_para(doc, "Core Cognee API Calls:", align="l", sz=1200, bold=True, color=NAVY, face="Calibri")]
    spTree.appendChild(make_textbox(doc, M, api_y - emu(0.32), emu(3.0), emu(0.3), label))

    for i, (fn, desc) in enumerate(apis):
        ax = api_sx + i * (api_w + api_gap)
        spTree.appendChild(make_rect(doc, ax, api_y, api_w, api_h, MID))
        p = [
            make_para(doc, fn,   align="ctr", sz=1200, bold=True, color=AMBER, face="Calibri"),
            make_para(doc, desc, align="ctr", sz=1050, color=ICE, face="Calibri"),
        ]
        spTree.appendChild(make_textbox(doc, ax, api_y + emu(0.12), api_w, api_h - emu(0.2), p, valign="ctr"))

    replace_spTree(doc, spTree)


# ---------------------------------------------------------------------------
# SLIDE 6 — Customer Relationships (The Features)
# ---------------------------------------------------------------------------
def build_slide6(doc):
    spTree = clear_spTree(doc)
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    build_slide_header(doc, spTree, "4. CUSTOMER RELATIONSHIPS",
                        "How Déjà establishes & maintains relationships with each customer segment")

    relationships = [
        (TEAL, "Students & Job Seekers", "Interactive Feedback Loop",
         ["Expectation: Dynamic, low-friction growth & habit tracking.",
          "Establish: Real-time journal ingestion (The Slate) with immediate background processing.",
          "Maintain: Active reinforcement. Thumbs up/down feedback on Oracle answers directly updates graph node weights in the backend, improving future Q&A recall accuracy."]),
        (MID, "Knowledge Workers", "Long-Term Cognitive Extension",
         ["Expectation: Secure, highly reliable, multi-year external brain.",
          "Establish: Dense context semantic graph indexing (top_k=150 context window) mapping complex project links.",
          "Maintain: Continuous semantic consistency. Keeps cross-referenced timeline records and graph notes synchronized over years, avoiding memory rot."]),
        (CORAL, "Wellness Seekers", "Private Safeguard Sanctuary",
         ["Expectation: Absolute data privacy, trust, and user sovereignty.",
          "Establish: Offline-first local mode (local SQLite & LanceDB) requiring no server connection.",
          "Maintain: GDPR-aligned 'right to be forgotten' via target memory branch wipes using cognee.forget(). Allows complete data pruning."]),
    ]

    card_w = emu(2.7)
    card_h = emu(3.18)
    gap = emu(0.2)
    total = 3 * card_w + 2 * gap
    sx = (W - total) // 2

    for i, (color, segment, rel_type, bullets) in enumerate(relationships):
        cx = sx + i * (card_w + gap)
        cy = emu(1.52)
        # Use card template but customize the title & subtitle manually for beauty
        spTree.appendChild(make_rect(doc, cx, cy, card_w, card_h, "F0F4FA", line_color="C5D5EA", line_w=9525))
        spTree.appendChild(make_rect(doc, cx, cy, card_w, emu(0.55), color))

        
        # Segment Header
        seg_paras = [make_para(doc, segment, align="ctr", sz=1300, bold=True, color=WHITE, face="Cambria")]
        spTree.appendChild(make_textbox(doc, cx, cy + emu(0.04), card_w, emu(0.48), seg_paras, valign="ctr"))
        
        # Relationship Type Sub-header
        sub_paras = [make_para(doc, rel_type, align="ctr", sz=1100, bold=True, color=color, face="Calibri")]
        spTree.appendChild(make_textbox(doc, cx, cy + emu(0.6), card_w, emu(0.3), sub_paras))
        
        # Bullets
        bullet_paras = []
        for b in bullets:
            bullet_paras.append(make_para(doc, b, bullet=True, sz=1100, color="212121", face="Calibri"))
        spTree.appendChild(make_textbox(doc, cx + emu(0.12), cy + emu(0.95), card_w - emu(0.24), card_h - emu(1.05), bullet_paras))

    replace_spTree(doc, spTree)



# ---------------------------------------------------------------------------
# SLIDE 7 — Revenue Streams
# ---------------------------------------------------------------------------
def build_slide7(doc):
    spTree = clear_spTree(doc)
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    build_slide_header(doc, spTree, "5. REVENUE STREAMS", "Free-first consumer model funded by B2B corporate wellness licensing")

    # Left Card: Free Core
    col_w = emu(3.75)
    col_h = emu(2.28)
    gap = emu(0.4)
    sx = (W - (2 * col_w + gap)) // 2
    
    # Free Tier Card
    spTree.appendChild(make_rect(doc, sx, emu(1.52), col_w, col_h, LGRAY, line_color="AAAAAA", line_w=9525))
    spTree.appendChild(make_rect(doc, sx, emu(1.52), col_w, emu(0.45), NAVY))
    t1_free = [make_para(doc, "Free Core Tier (Free Forever)", align="ctr", sz=1300, bold=True, color=WHITE, face="Cambria")]
    spTree.appendChild(make_textbox(doc, sx, emu(1.52 + 0.05), col_w, emu(0.35), t1_free, valign="ctr"))
    
    p_free = [make_para(doc, "₹0 / month  •  Consumer Mainstream Tier", align="ctr", sz=1100, bold=True, color=TEAL, face="Calibri")]
    spTree.appendChild(make_textbox(doc, sx, emu(2.02), col_w, emu(0.3), p_free))
    
    bullets_free = [
        "Local-only graph storage (SQLite) & vector embedding (LanceDB).",
        "Zero server hosting overhead for the company (client-side execution).",
        "Unlimited Slate journal entries & manual Oracle Q&A queries."
    ]
    bf_paras = []
    for b in bullets_free:
        bf_paras.append(make_para(doc, b, bullet=True, sz=1050, color="212121", face="Calibri"))
    spTree.appendChild(make_textbox(doc, sx + emu(0.12), emu(2.32), col_w - emu(0.24), col_h - emu(0.85), bf_paras))

    # Pro Tier Card
    pro_x = sx + col_w + gap
    spTree.appendChild(make_rect(doc, pro_x, emu(1.52), col_w, col_h, "F0F4FA", line_color="C5D5EA", line_w=9525))
    spTree.appendChild(make_rect(doc, pro_x, emu(1.52), col_w, emu(0.45), MID))
    t1_pro = [make_para(doc, "Pro Tier (The Game Changer)", align="ctr", sz=1300, bold=True, color=WHITE, face="Cambria")]
    spTree.appendChild(make_textbox(doc, pro_x, emu(1.52 + 0.05), col_w, emu(0.35), t1_pro, valign="ctr"))
    
    p_pro = [make_para(doc, "₹149 / month ($1.99/mo)  •  Cloud Premium", align="ctr", sz=1100, bold=True, color=AMBER, face="Calibri")]
    spTree.appendChild(make_textbox(doc, pro_x, emu(2.02), col_w, emu(0.3), p_pro))
    
    bullets_pro = [
        "Seamless Multi-Device Sync & secure roaming via Cognee Cloud.",
        "Proactive continuous Blindspots analysis pushing real-time Paradox Alerts.",
        "Advanced Oracle reasoning using premium high-scale LLM synthesis."
    ]
    bp_paras = []
    for b in bullets_pro:
        bp_paras.append(make_para(doc, b, bullet=True, sz=1050, color="212121", face="Calibri"))
    spTree.appendChild(make_textbox(doc, pro_x + emu(0.12), emu(2.32), col_w - emu(0.24), col_h - emu(0.85), bp_paras))

    # Bottom Panel: B2B2C Corporate Wellness Model
    panel_y = emu(3.95)
    panel_w = W - 2*M
    panel_h = emu(0.9)
    spTree.appendChild(make_rect(doc, M, panel_y, panel_w, panel_h, "FFFDF2", line_color="EAD4A2", line_w=9525))
    spTree.appendChild(make_rect(doc, M, panel_y, emu(0.08), panel_h, AMBER))
    
    t_panel = [make_para(doc, "B2B2C Corporate Wellness Model (Primary Monetization Engine)", sz=1200, bold=True, color=NAVY, face="Cambria")]
    spTree.appendChild(make_textbox(doc, M + emu(0.2), panel_y + emu(0.05), panel_w - emu(0.3), emu(0.3), t_panel))
    
    b_panel = [
        make_para(doc, "• EAP Integrations: Employers buy sponsored bulk seats of Déjà Pro for employee mental health, habit tracking & stress analysis.", sz=1050, color="212121", face="Calibri"),
        make_para(doc, "• API Licensing: White-label semantic recovery API integration for wellness app partners & journaling communities.", sz=1050, color="212121", face="Calibri")
    ]
    spTree.appendChild(make_textbox(doc, M + emu(0.2), panel_y + emu(0.35), panel_w - emu(0.3), emu(0.5), b_panel))

    replace_spTree(doc, spTree)



# ---------------------------------------------------------------------------
# SLIDE 8 — Key Resources
# ---------------------------------------------------------------------------
def build_slide8(doc):
    spTree = clear_spTree(doc)
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    build_slide_header(doc, spTree, "6. KEY RESOURCES", "Infrastructure that makes Déjà possible")

    resources = [
        (MID,   "Technology Stack",
         ["Python FastAPI — memory bridge service",
          "Node.js Express — API gateway & auth",
          "React + Vite — glassmorphism frontend",
          "Cognee SDK — semantic graph engine",
          "SQLite + LanceDB — local vector storage",
          "Supabase — chronological DB & Auth"]),
        (TEAL,  "AI & Cognee Integration",
         ["Cognee Open Source (Python library)",
          "Cognee Cloud — hosted semantic graphs",
          "LiteLLM wrapper — multi-LLM support",
          "Gemini Flash Lite — low-latency inference",
          "gemini-embedding-001 — 768-dim vectors",
          "Auth0 Device Flow — cloud provisioning"]),
        (CORAL, "Human & IP Resources",
         ["Concurrency-safe async queue (SQLite lock fix)",
          "Custom hybrid retrieval shortcut (10× speed)",
          "Blindspots algorithm (graph vs. timeline diff)",
          "Supabase RLS schema (multi-tenant security)",
          "Dockerized deployment for Hugging Face / Render",
          "Comprehensive test suite (cognee, recall, speed)"]),
    ]

    rw = emu(2.7)
    rh = emu(3.4)
    rg = emu(0.17)
    total = 3*rw + 2*rg
    sx = (W - total) // 2

    for i, (color, title, bullets) in enumerate(resources):
        rx = sx + i * (rw + rg)
        build_card(doc, spTree, rx, emu(1.35), rw, rh, title, bullets, hdr_color=color)

    replace_spTree(doc, spTree)


# ---------------------------------------------------------------------------
# SLIDE 9 — Key Activities (Cognee Usage deep-dive)
# ---------------------------------------------------------------------------
def build_slide9(doc):
    spTree = clear_spTree(doc)
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    build_slide_header(doc, spTree, "7. KEY ACTIVITIES — COGNEE DEEP DIVE",
                        "How Déjà maximises Cognee's capabilities across every feature")

    rows = [
        (AMBER,  "Journal Ingest Pipeline",
         "User submits text → Node.js gateway → FastAPI bridge → cognee.add() classifies entities → cognee.cognify() builds knowledge graph → vectors stored in LanceDB"),
        (TEAL,   "Oracle Query Pipeline",
         "User asks question → cognee.recall(top_k=150) traverses graph → raw nodes returned → local LiteLLM analyzer summarizes → response in ~1.5s (bypasses default Cognee LLM round-trip)"),
        (MID,    "Blindspots Detection",
         "Supabase timeline entries fetched → Cognee graph node density computed → cosine vector distance analysis → chronological gaps & contradictions surfaced as 'paradox alerts'"),
        (CORAL,  "Memory Safeguard",
         "Target topic identified → cognee.forget() severs semantic edges and prunes vector space → or cognee.prune for full graph wipe → confirmation returned to UI"),
    ]

    rh = emu(0.72)
    ry = emu(1.35)
    label_w = emu(1.95)
    desc_w = W - 2*M - label_w - emu(0.2)

    for i, (color, label, desc) in enumerate(rows):
        cy = ry + i * (rh + emu(0.1))
        spTree.appendChild(make_rect(doc, M, cy, label_w, rh, color))
        lp = [make_para(doc, label, align="ctr", sz=1150, bold=True, color=WHITE, face="Calibri")]
        spTree.appendChild(make_textbox(doc, M, cy + emu(0.07), label_w, rh - emu(0.08), lp, valign="ctr"))
        spTree.appendChild(make_rect(doc, M + label_w + emu(0.2), cy, desc_w, rh, "F0F4FA", line_color="C5D5EA", line_w=6350))
        dp = [make_para(doc, desc, sz=1050, color="212121", face="Calibri")]
        spTree.appendChild(make_textbox(doc, M + label_w + emu(0.3), cy + emu(0.08), desc_w - emu(0.2), rh - emu(0.08), dp))

    # Highlight note — positioned after all rows
    hl = [make_para(doc, "Production concurrency: Serialized async queue prevents SQLite write-lock contention during peak ingestion — ready for enterprise load.",
                     sz=1050, bold=True, color=MID, face="Calibri")]
    spTree.appendChild(make_textbox(doc, M, emu(4.82), W-2*M, emu(0.3), hl))


    replace_spTree(doc, spTree)


# ---------------------------------------------------------------------------
# SLIDE 10 — Key Partners
# ---------------------------------------------------------------------------
def build_slide10(doc):
    spTree = clear_spTree(doc)
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    build_slide_header(doc, spTree, "8. KEY PARTNERS", "Ecosystem that powers Déjà")

    partners = [
        (TEAL,  "Cognee AI",
         ["Primary AI memory partner",
          "Open Source Python SDK (cognee library)",
          "Cognee Cloud — hosted semantic graph service",
          "Auth0 device-code flow for user provisioning"]),
        (MID,   "Google / Gemini",
         ["LLM: gemini/gemini-3.1-flash-lite",
          "Embedding: gemini-embedding-001 (768-dim)",
          "Low-latency inference for Oracle responses",
          "Via LiteLLM multi-provider wrapper"]),
        (CORAL, "Supabase",
         ["PostgreSQL chronological timeline store",
          "Row-Level Security (RLS) multi-tenancy",
          "Built-in Auth for session management",
          "Anon key access from React frontend"]),
        (AMBER, "Deployment & Infra",
         ["Hugging Face Spaces — primary hosting",
          "Render — alternate cloud deployment",
          "Docker — unified multi-process container",
          "LanceDB — local vector storage engine"]),
    ]

    pw = emu(1.95)
    ph = emu(3.15)
    pg = emu(0.16)
    total = 4*pw + 3*pg
    sx = (W - total) // 2

    for i, (color, title, bullets) in enumerate(partners):
        px = sx + i * (pw + pg)
        build_card(doc, spTree, px, emu(1.35), pw, ph, title, bullets, hdr_color=color)

    replace_spTree(doc, spTree)


# ---------------------------------------------------------------------------
# SLIDE 11 — Cost Structure
# ---------------------------------------------------------------------------
def build_slide11(doc):
    spTree = clear_spTree(doc)
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    build_slide_header(doc, spTree, "9. COST STRUCTURE", "Lean AI-native architecture with managed infrastructure")

    # Left: cost categories as bar chart approximation
    categories = [
        (TEAL,  "Cognee Cloud API",       "Usage-based per query/ingest beyond free tier"),
        (MID,   "LLM & Embedding API",    "Gemini Flash Lite — among lowest cost LLMs available"),
        (AMBER, "Supabase (Database)",    "Free tier covers early users; Pro ~$25/mo at scale"),
        (CORAL, "Hosting (HF / Render)",  "Free tier on Hugging Face Spaces; Render ~$7/mo"),
        (LGRAY, "Development & DevOps",   "Open source toolchain; minimal licensing costs"),
    ]

    bx = M
    by = emu(1.4)
    bh = emu(0.55)
    bg = emu(0.12)

    # Label column and bar column
    label_w = emu(1.8)
    bar_max  = emu(4.8)
    bar_widths = [0.8, 0.55, 0.35, 0.20, 0.10]  # relative widths

    for i, ((color, name, desc), rel) in enumerate(zip(categories, bar_widths)):
        cy = by + i * (bh + bg)
        # Label
        lp = [make_para(doc, name, align="r", sz=1150, bold=True, color=NAVY, face="Calibri")]
        spTree.appendChild(make_textbox(doc, M, cy, label_w, bh, lp, valign="ctr"))
        # Bar
        bar_w = int(bar_max * rel)
        spTree.appendChild(make_rect(doc, M + label_w + emu(0.15), cy + emu(0.1), bar_w, bh - emu(0.18), color))
        # Desc
        dp = [make_para(doc, desc, sz=1050, color=DKGRAY, face="Calibri")]
        spTree.appendChild(make_textbox(doc, M + label_w + emu(0.15), cy + bh - emu(0.08),
                                         bar_max + emu(0.5), emu(0.4), dp))

    # Right panel — cost model summary
    rx = M + emu(7.0)
    ry = emu(1.35)
    rw = W - M - rx
    spTree.appendChild(make_rect(doc, rx, ry, rw, emu(3.4), MID))
    summary = [
        make_para(doc, "Cost Model", align="ctr", sz=1500, bold=True, color=WHITE, face="Cambria"),
        make_para(doc, "", sz=800, color=WHITE, face="Calibri"),
        make_para(doc, "~$0", align="ctr", sz=3200, bold=True, color=AMBER, face="Cambria"),
        make_para(doc, "bootstrapped MVP cost", align="ctr", sz=1050, color=ICE, face="Calibri"),
        make_para(doc, "", sz=800, color=WHITE, face="Calibri"),
        make_para(doc, "Variable cost scales", align="ctr", sz=1100, color=WHITE, face="Calibri"),
        make_para(doc, "with user growth only", align="ctr", sz=1100, color=WHITE, face="Calibri"),
    ]
    spTree.appendChild(make_textbox(doc, rx + emu(0.1), ry + emu(0.15), rw - emu(0.2), emu(3.1), summary, valign="ctr"))

    replace_spTree(doc, spTree)


# ---------------------------------------------------------------------------
# SLIDE 12 — Why We Win / Competitive Advantage
# ---------------------------------------------------------------------------
def build_slide12(doc):
    spTree = clear_spTree(doc)
    spTree.appendChild(make_rect(doc, 0, 0, W, H, WHITE))
    build_slide_header(doc, spTree, "WHY DÉJÀ WINS — BEST USE OF COGNEE",
                        "Demonstrating the full power of Cognee in a real-world production system")

    points = [
        (MID,   "1. Dual Local + Cloud Architecture",
         "First app to seamlessly switch between Cognee Open Source (SQLite/LanceDB) and Cognee Cloud — proving the SDK's full versatility."),
        (TEAL,  "2. Auth0 Device Flow Integration",
         "Extended Cognee's ecosystem with an automated onboarding script (auth_cognee.py) using Cognee's device code flow — zero user friction."),
        (CORAL, "3. Graph-Timeline Comparison Engine",
         "Blindspots cross-references Supabase's relational timeline against Cognee's structural node density — a novel use of graph topology for personal insight."),
        (AMBER, "4. Production Concurrency Solutions",
         "Solved SQLite write-lock contention via serialized async queue — a real enterprise-grade fix that makes Cognee viable under concurrent load."),
    ]

    pw = emu(8.2)
    ph = emu(0.82)
    px = M
    py = emu(1.4)

    for i, (color, title, desc) in enumerate(points):
        cy = py + i * (ph + emu(0.15))
        spTree.appendChild(make_rect(doc, px, cy, emu(0.08), ph, color))
        spTree.appendChild(make_rect(doc, px + emu(0.1), cy, pw - emu(0.1), ph, "F0F4FA", line_color="C5D5EA", line_w=6350))
        tp = [
            make_para(doc, title, sz=1300, bold=True, color=NAVY, face="Cambria"),
            make_para(doc, desc,  sz=1150, color="333333", face="Calibri"),
        ]
        spTree.appendChild(make_textbox(doc, px + emu(0.25), cy + emu(0.06), pw - emu(0.35), ph - emu(0.1), tp))

    replace_spTree(doc, spTree)


# ---------------------------------------------------------------------------
# SLIDE 13 — Thank You / Conclusion
# ---------------------------------------------------------------------------
def build_slide13(doc):
    spTree = clear_spTree(doc)
    # Dark background
    spTree.appendChild(make_rect(doc, 0, 0, W, H, NAVY))
    spTree.appendChild(make_rect(doc, 0, H - emu(0.25), W, emu(0.25), AMBER))

    # Central content
    t1 = [make_para(doc, "Thank You", align="ctr", sz=6000, bold=True, color=WHITE, face="Cambria")]
    spTree.appendChild(make_textbox(doc, M, emu(0.7), W - 2*M, emu(1.1), t1, valign="ctr"))

    t2 = [make_para(doc, "Déjà — Cognee-Powered Memory Recovery Engine", align="ctr", sz=1600, color=ICE, face="Calibri")]
    spTree.appendChild(make_textbox(doc, M, emu(1.9), W - 2*M, emu(0.5), t2))

    # Three takeaway boxes
    takeaways = [
        (TEAL,  "🧠 Semantic Memory", "Personal AI memory graph\npowered by Cognee"),
        (MID,   "🔮 Natural Language", "Ask anything about\nyour past in plain English"),
        (CORAL, "🔒 Privacy First",    "Local + Cloud modes;\nright to be forgotten"),
    ]

    tw = emu(2.55)
    th = emu(1.3)
    tg = emu(0.2)
    total = 3*tw + 2*tg
    tx_start = (W - total) // 2

    for i, (color, title, desc) in enumerate(takeaways):
        tx = tx_start + i * (tw + tg)
        ty = emu(2.6)
        spTree.appendChild(make_rect(doc, tx, ty, tw, th, color))
        tp = [
            make_para(doc, title, align="ctr", sz=1400, bold=True, color=WHITE, face="Cambria"),
            make_para(doc, desc,  align="ctr", sz=1100, color=ICE, face="Calibri"),
        ]
        spTree.appendChild(make_textbox(doc, tx, ty + emu(0.1), tw, th - emu(0.1), tp, valign="ctr"))

    # Links / contact
    links = [
        make_para(doc, "GitHub · Hugging Face Spaces · CMR ThinkFest 3.0 — Team Déjà", align="ctr", sz=1100, color=ICE, face="Calibri"),
        make_para(doc, "SDG 3: Good Health & Well-Being  |  SDG 9: Industry, Innovation & Infrastructure", align="ctr", sz=1000, color=AMBER, face="Calibri"),
    ]
    spTree.appendChild(make_textbox(doc, M, emu(4.1), W - 2*M, emu(0.55), links))

    replace_spTree(doc, spTree)


# ---------------------------------------------------------------------------
# Patch slide IDs to avoid duplicates from clear_spTree
# ---------------------------------------------------------------------------
_id_counter = 100

def patch_ids(doc):
    global _id_counter
    for el in doc.getElementsByTagName("*"):
        if el.hasAttribute("id") and el.getAttribute("name") in ("", "TextBox", "Rect", "Line"):
            el.setAttribute("id", str(_id_counter))
            _id_counter += 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
BUILDERS = {
    "slide1.xml":  build_slide1,
    "slide2.xml":  build_slide2,
    "slide3.xml":  build_slide3,
    "slide4.xml":  build_slide4,
    "slide5.xml":  build_slide5,
    "slide6.xml":  build_slide6,
    "slide7.xml":  build_slide7,
    "slide8.xml":  build_slide8,
    "slide9.xml":  build_slide9,
    "slide10.xml": build_slide10,
    "slide11.xml": build_slide11,
    "slide12.xml": build_slide12,
    "slide13.xml": build_slide13,
}

def main():
    slides_dir = os.path.join(UNPACK, "ppt", "slides")
    for fname, builder in BUILDERS.items():
        path = os.path.join(slides_dir, fname)
        if not os.path.exists(path):
            print(f"  [SKIP] {fname} not found")
            continue
        doc = read_xml(path)
        builder(doc)
        patch_ids(doc)
        write_xml(doc, path)
        print(f"  [OK] {fname}")

    # Re-zip
    if os.path.exists(OUT):
        os.remove(OUT)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(UNPACK):
            for file in files:
                abs_path = os.path.join(root, file)
                arc_path = os.path.relpath(abs_path, UNPACK)
                zf.write(abs_path, arc_path)
    print(f"\n✅  Written: {OUT}")

if __name__ == "__main__":
    main()
