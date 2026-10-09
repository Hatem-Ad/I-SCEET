"""
================================================================================
 I-SCEET — SDDD Builder v1.0
 File: orchestrator/sddd_builder.py
 Copyright (c) 2026 Hatem Adouani — MIT License
================================================================================
 Parses M2 LLM text output -> generates professional SDDD-0xx.docx

 IMPORTANT: this module is intentionally independent from srd_builder.py.
 An LLR is NOT an HLR — different fields, different table structure
 (Causes/Effects with CAUSE:/SUBCAUSE:/EFFECT: nesting vs. flat metadata),
 different Design-Traceability semantics (Refined/Extended/Derived vs.
 Upwards Traceability). Do not attempt to merge these back together.

 Expected M2 raw text format (already validated, per project convention):

   SECTION 1.0 — INTRODUCTION
   SECTION 2.0 — ARCHITECTURE
   SECTION 3.0 — REFERENCED DOCUMENTS
   SECTION 4.0 — LOW-LEVEL REQUIREMENTS

     ---FUNCTION_START---
     Prototype: <C prototype>
     Parameters: <R/W/R-W list>
     Pre-conditions: <...>
     Called Functions: <...>
     Input Data: <...>
     Output Data: <...>

     LLR-<SUBSYSTEM>-NNN
     [COV.HLR-xxx] and/or [JUS.[Rxx] section]
     <Capability / function name>

     CAUSE: ...
       SUBCAUSE: ...
       EFFECT: ...
     ...

     [Bracketed label]: narrative sentence...
     ...

     Design-Traceability: Refined | Extended | Derived
     Mean-of-Verification: ...
     Rationale: ...
     [END_REQ]
     ---FUNCTION_END---

   SECTION 5.0 — DERIVED REQUIREMENTS SUMMARY   (optional, consolidated
                                                  automatically if absent)

 NOTE: this is a first version built without a real M2 v3.1 output sample
 in hand — the parser is defensive (falls back to raw-text dump per
 section/function rather than silently producing blank pages) but MUST be
 validated against a real generation and adjusted if the actual model
 output deviates from the format above.
================================================================================
"""

import os
import re
from datetime import datetime

try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    raise ImportError("python-docx required: pip install python-docx")

# ── STYLE CONSTANTS (own set — independent from srd_builder.py) ────────────────
BLUE     = RGBColor(0x1F, 0x38, 0x64)
MID_BLUE = RGBColor(0x2E, 0x75, 0xB6)
GRAY     = RGBColor(0x66, 0x66, 0x66)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
FONT_NAME = "Arial"

ID_BLUE      = RGBColor(0x3B, 0x82, 0xF6)  # LLR-xxx heading, [END_REQ] marker
DARK_TITLE   = RGBColor(0x1C, 0x1C, 0x1C)  # capability/function title, Requirement heading
BLACK        = RGBColor(0x00, 0x00, 0x00)
TRACE_GREEN  = RGBColor(0x1E, 0x7A, 0x34)  # Design-Traceability value accent
CAUSE_BG     = "DCE6F1"                    # light blue — cause condition cells
CE_HEADER_BG = "84ABD5"                    # medium blue — Cause/Effect row-label header
NAVY_BG      = "1F3864"                    # dark navy — Parameters table header
COV_BLUE     = RGBColor(0x2E, 0x75, 0xB6)  # [COV.xxx] tag color
JUS_GREEN    = RGBColor(0x77, 0xBC, 0x65)  # [JUS.xxx] tag color
SERIF_FONT   = "Liberation Serif"

# Function-header fields (per FUNCTION_START block, before any LLR)
FUNCTION_FIELDS = [
    'Prototype', 'Parameters', 'Pre-conditions', 'Called Functions',
    'Input Data', 'Output Data',
]

# Per-LLR trailing metadata fields (colon-labeled, easy to extract)
LLR_META_FIELDS = ['Design-Traceability', 'Mean-of-Verification', 'Rationale']


# ── TEXT CLEANUP ──────────────────────────────────────────────────────────────
def _strip_think_tags(text: str) -> str:
    if not text:
        return text
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'</?think>', '', cleaned)
    return cleaned.strip()


# ── DOCX HELPERS (styling — kept close to SRD look for visual consistency,
#    but copied locally so SDDD can diverge independently later) ───────────────
def _set_cell_bg(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def _add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.name = FONT_NAME
    if level == 1:
        run.font.size = Pt(16)
        run.font.color.rgb = BLUE
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after  = Pt(6)
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '6')
        bottom.set(qn('w:color'), '2E75B6')
        pBdr.append(bottom)
        pPr.append(pBdr)
    elif level == 2:
        run.font.size = Pt(13)
        run.font.color.rgb = MID_BLUE
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after  = Pt(4)
    elif level == 3:
        run.font.size = Pt(11.5)
        run.font.color.rgb = MID_BLUE
        run.italic = True
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after  = Pt(3)
    return p


def _add_body(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = Pt(11)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after  = Pt(3)
    return p


def _add_bullet(doc, text):
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = Pt(11)
    return p


def _add_header_footer(doc, doc_id, version, date_str):
    section = doc.sections[0]
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    hp.clear()
    run = hp.add_run(f"{doc_id}   |   I-SCEET   |   v{version}   |   DRAFT")
    run.font.name = FONT_NAME
    run.font.size = Pt(9)
    run.font.color.rgb = GRAY
    pPr = hp._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'), 'single')
    bot.set(qn('w:sz'), '6')
    bot.set(qn('w:color'), '2E75B6')
    pBdr.append(bot)
    pPr.append(pBdr)

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    fp.clear()
    run2 = fp.add_run(f"I-SCEET — AI-generated draft, engineering review required   |   {date_str}")
    run2.font.name = FONT_NAME
    run2.font.size = Pt(9)
    run2.font.color.rgb = GRAY
    pPr2 = fp._p.get_or_add_pPr()
    pBdr2 = OxmlElement('w:pBdr')
    top = OxmlElement('w:top')
    top.set(qn('w:val'), 'single')
    top.set(qn('w:sz'), '6')
    top.set(qn('w:color'), '2E75B6')
    pBdr2.append(top)
    pPr2.append(pBdr2)


def _make_cover(doc, doc_id, title, version, project, author, date_str, dal):
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_title.add_run(title)
    r.bold = True
    r.font.size = Pt(28)
    r.font.color.rgb = BLUE
    r.font.name = FONT_NAME
    p_title.paragraph_format.space_before = Pt(60)
    p_title.paragraph_format.space_after  = Pt(8)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p_sub.add_run("Intelligent Safety-Critical Engineering Environment Toolchain")
    r2.font.size = Pt(14)
    r2.font.color.rgb = GRAY
    r2.font.name = FONT_NAME
    r2.italic = True
    p_sub.paragraph_format.space_after = Pt(30)

    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    rows_data = [
        ("Document ID",  doc_id),
        ("Version",      version),
        ("Status",       "DRAFT"),
        ("Date",         date_str),
        ("Author",       author),
        ("Project",      project),
        ("DAL Level",    dal),
        ("Standard",     "RTCA DO-178C §5 / §11.10"),
    ]
    for i, (key, val) in enumerate(rows_data):
        row = table.add_row()
        row.cells[0].text = key
        row.cells[1].text = val
        row.cells[0].width = Cm(5)
        row.cells[1].width = Cm(10)
        _set_cell_bg(row.cells[0], "1F3864" if i == 0 else "F2F2F2")
        run_k = row.cells[0].paragraphs[0].runs[0]
        run_k.bold = True
        run_k.font.name = FONT_NAME
        run_k.font.size = Pt(10)
        run_k.font.color.rgb = WHITE if i == 0 else MID_BLUE
        run_v = row.cells[1].paragraphs[0].runs[0]
        run_v.font.name = FONT_NAME
        run_v.font.size = Pt(10)

    doc.add_page_break()


def _make_revision_table(doc, version, date_str, generator="M2 (I-SCEET AI)"):
    _add_heading(doc, "Document Revision History")
    table = doc.add_table(rows=1, cols=4)
    headers = ["Version", "Date", "Author", "Description"]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        _set_cell_bg(cell, "1F3864")
        r = cell.paragraphs[0].runs[0]
        r.bold = True
        r.font.color.rgb = WHITE
        r.font.name = FONT_NAME
        r.font.size = Pt(10)

    row = table.add_row()
    vals = [str(version), date_str, generator, "AI-generated document"]
    for j, v in enumerate(vals):
        row.cells[j].text = v
        row.cells[j].paragraphs[0].runs[0].font.size = Pt(10)
        row.cells[j].paragraphs[0].runs[0].font.name = FONT_NAME

    doc.add_paragraph()


def _add_pipe_table(doc, lines: list):
    """Render markdown-style '| a | b | c |' lines as a real Word table."""
    rows = []
    for l in lines:
        l = l.strip()
        if not l.startswith('|'):
            continue
        cells = [c.strip() for c in l.strip('|').split('|')]
        if all(re.fullmatch(r'-+', c) for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return False

    ncols = max(len(r) for r in rows)
    tbl = doc.add_table(rows=0, cols=ncols)
    for i, row_vals in enumerate(rows):
        row = tbl.add_row()
        for j in range(ncols):
            text = row_vals[j] if j < len(row_vals) else ""
            row.cells[j].text = text
            if row.cells[j].paragraphs[0].runs:
                run = row.cells[j].paragraphs[0].runs[0]
                run.font.name = FONT_NAME
                run.font.size = Pt(9.5)
                if i == 0:
                    run.bold = True
                    run.font.color.rgb = WHITE
            if i == 0:
                _set_cell_bg(row.cells[j], "1F3864")
            elif i % 2 == 0:
                _set_cell_bg(row.cells[j], "F2F2F2")
    doc.add_paragraph()
    return True


def _render_multiline_field(doc, content: str, allow_subheadings: bool = False):
    if not content or not content.strip():
        _add_body(doc, "None")
        return
    lines = [l for l in content.split('\n') if l.strip()]
    # Drop stray markdown heading markers with no attached text (leftover
    # from '## SECTION x.0' prefixes at section boundaries).
    lines = [l for l in lines if not re.fullmatch(r'#{1,6}\s*', l.strip())]
    pipe_lines = [l for l in lines if l.strip().startswith('|')]
    if len(pipe_lines) >= 2:
        _add_pipe_table(doc, lines)
        remaining = [l for l in lines if not l.strip().startswith('|')]
        for l in remaining:
            _add_body(doc, _clean_markdown_inline(l.strip()))
    else:
        for l in lines:
            l = l.strip()
            if allow_subheadings and re.match(r'#{2,4}\s+\S', l):
                heading_text = re.sub(r'^#{2,4}\s+', '', l)
                _add_heading(doc, _clean_markdown_inline(heading_text), 3)
            elif l.startswith('-') or l.startswith('•'):
                _add_bullet(doc, _clean_markdown_inline(l.lstrip('-• ')))
            else:
                _add_body(doc, _clean_markdown_inline(l))


def _add_id_heading(doc, id_text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(id_text)
    run.bold = True
    run.italic = True
    run.font.name = FONT_NAME
    run.font.size = Pt(11)
    run.font.color.rgb = ID_BLUE
    return p


def _add_italic_blue(doc, text: str, size: float = 9.5, color=None):
    if color is None:
        color = MID_BLUE
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(0)
    run = p.add_run(text)
    run.italic = True
    run.font.name = FONT_NAME
    run.font.size = Pt(size)
    run.font.color.rgb = color
    return p


def _add_bold_italic_title(doc, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.italic = True
    run.font.name = FONT_NAME
    run.font.size = Pt(11.5)
    return p


def _add_horizontal_rule(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run("")
    run.font.size = Pt(2)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '4')
    bottom.set(qn('w:color'), 'AAAAAA')
    pBdr.append(bottom)
    pPr.append(pBdr)


def _add_field_line(doc, label: str, value: str, tab_pos_cm: float = 6.5,
                     value_color=None):
    p = doc.add_paragraph()
    p.paragraph_format.tab_stops.add_tab_stop(Cm(tab_pos_cm))
    p.paragraph_format.left_indent      = Cm(tab_pos_cm)
    p.paragraph_format.first_line_indent = Cm(-tab_pos_cm)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(f"{label}\t{value}")
    run.italic = True
    run.font.name = SERIF_FONT
    run.font.size = Pt(10)
    run.font.color.rgb = value_color or BLACK
    return p


def _add_borderless_field_list(doc, pairs: list):
    for label, value, *color in pairs:
        if not value:
            continue
        c = color[0] if color else None
        _add_field_line(doc, label, value, value_color=c)


# ── PARSER — real LLR/FUNCTION format (NOT the HLR field set) ──────────────────
def _clean_field_value(value: str) -> str:
    if not value:
        return value
    cut_patterns = [
        r'\n\s*-{3,}',
        r'\[END_REQ\]',
        r'---FUNCTION_END---',
        r'\n\s*(?:CAUSE|SUBCAUSE|EFFECT):',
        r'\n\s*LLR-[A-Z]+-\d+(?:-\d+)?',
    ]
    earliest = len(value)
    for pat in cut_patterns:
        m = re.search(pat, value)
        if m and m.start() < earliest:
            earliest = m.start()
    return value[:earliest].strip()


def _parse_labeled_fields(block: str, fields: list, extra_stop_patterns: list = None) -> dict:
    """Boundary-aware extraction of 'Field: value' lines for a given field
    list (works for both FUNCTION_FIELDS and LLR_META_FIELDS).
    extra_stop_patterns: additional regex alternatives (already valid inside
    a non-capturing group) that should also terminate a field's value —
    e.g. the start of the next LLR block, so 'Output Data:' doesn't swallow
    the whole LLR content that follows it."""
    out = {}
    stops = [re.escape(f) + ':' for f in fields]
    stops += [r'\[END_REQ\]', r'---FUNCTION_(?:START|END)---', r'#{2,4}\s',
              r'\[VAR\]', r'\[CONST\]', r'\[TYPE\]']
    if extra_stop_patterns:
        stops += extra_stop_patterns
    boundary = '(?:' + '|'.join(stops) + ')'
    for field in fields:
        pattern = rf'{re.escape(field)}:\s*(.*?)(?=\n\s*{boundary}|\Z)'
        m = re.search(pattern, block, re.DOTALL)
        raw_value = m.group(1).strip() if m else ''
        out[field] = _clean_field_value(raw_value)
    return out


def _parse_causes_effects(text: str) -> list:
    """Parse a Causes/Effects table into row-groups for rendering.

    Primary format (confirmed on real M2 output): a markdown pipe table
        | Causes | Effects |
        |--------|---------|
        | source == HSE | [Configure High-Speed External Clock] |
        |               | [Some unconditional effect]           |

    Fallback format (in case a future prompt revision reintroduces it):
    CAUSE:/SUBCAUSE:/EFFECT: text markers with implicit nesting.

    Returns list of dicts: {'cause', 'subcause', 'effect', 'group_first'}
    """
    lines = [l.rstrip() for l in text.split('\n') if l.strip()]

    # ── Try the 4-column alias-separated format first (real M2 output,
    # mirrors the original template's explicit Cause Alias/Effect Alias
    # columns): | Cause Alias | Cause Writing Block | Effect Alias | Effect Writing Block |
    alias4_rows = []
    in_table4 = False
    for line in lines:
        stripped = line.strip()
        if re.match(r'\|\s*Cause\s*Alias\s*\|\s*Cause\s*Writing\s*Block\s*\|'
                    r'\s*Effect\s*Alias\s*\|\s*Effect\s*Writing\s*Block\s*\|',
                    stripped, re.IGNORECASE):
            in_table4 = True
            continue
        if not in_table4:
            continue
        if re.fullmatch(r'\|[\s\-|]+\|', stripped):
            continue
        cells = [c.strip() for c in stripped.strip('|').split('|')]
        if len(cells) != 4:
            in_table4 = False
            continue
        c_alias, c_text, e_alias, e_text = cells
        # Re-embed the alias into the cause/effect text as "[Cn] text" /
        # "[En] text" - this is exactly the shape the rest of the
        # pipeline (rendering + Implementation-line alias matching)
        # already expects, so nothing downstream needs to change to
        # support this alternate input table shape.
        cause_full = f"[{c_alias}] {c_text.strip('[]')}" if c_alias else c_text
        effect_full = f"[{e_alias}] {e_text.strip('[]')}" if e_alias else (e_text or 'No effect')
        alias4_rows.append({'cause': cause_full, 'subcause': '', 'effect': effect_full, 'group_first': True})
    if alias4_rows:
        return alias4_rows

    # ── Try markdown pipe-table format first ───────────────────────────────
    pipe_rows = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if re.match(r'\|\s*Causes?\s*\|\s*Effects?\s*\|', stripped, re.IGNORECASE):
            in_table = True
            continue
        if not in_table:
            continue
        if re.fullmatch(r'\|[\s\-|]+\|', stripped):
            continue  # separator row
        m = re.match(r'\|(.*)\|(.*)\|\s*$', stripped)
        if m:
            cause = m.group(1).strip()
            effect = m.group(2).strip() or 'No effect'
            pipe_rows.append({'cause': cause, 'subcause': '', 'effect': effect, 'group_first': True})
        else:
            in_table = False  # table region ended
    if pipe_rows:
        return pipe_rows

    # ── Fallback: CAUSE:/SUBCAUSE:/EFFECT: marker syntax ───────────────────
    rows = []
    for line in lines:
        m = re.match(r'(CAUSE|SUBCAUSE|EFFECT)\s*:\s*(.*)$', line.strip(), re.IGNORECASE)
        if not m:
            continue
        kind, val = m.group(1).upper(), m.group(2).strip()
        if kind == 'CAUSE':
            rows.append({'cause': val, 'subcause': '', 'effect': '', 'group_first': True})
        elif kind == 'SUBCAUSE':
            rows.append({'cause': '', 'subcause': val, 'effect': '', 'group_first': False})
        elif kind == 'EFFECT':
            if rows:
                if rows[-1]['effect']:
                    rows[-1]['effect'] += '\n' + val
                else:
                    rows[-1]['effect'] = val
            else:
                rows.append({'cause': '', 'subcause': '', 'effect': val, 'group_first': False})
    return rows


_NARRATIVE_SKIP_PATTERNS = [
    r'^\|',                                    # causes/effects table row
    r'^(CAUSE|SUBCAUSE|EFFECT)\s*:',           # marker-syntax table (fallback format)
    r'^(Design-)?Traceability\s*:',
    r'^Mean-of-Verification\s*:',
    r'^Rationale\s*:',
    r'^\[END_REQ\]',
    r'^LLR-[A-Z]+-\d+(?:-\d+)?',
    r'^\[(COV|JUS)\.',
    r'^\[(VAR|CONST|TYPE)\]',
    r'^Implementation\s*:?\s*$',
    r'^Narrative\s*:?\s*$',
    r'^Causes\s*/\s*Effects\s*:?\s*$',
]


def _extract_narrative(text: str, exclude_title: str = '') -> list:
    """Extract the narrative paragraph(s) of an LLR: free prose sitting
    between the Causes/Effects table and the trailing meta fields.

    Handles both the '[Bracketed label]: sentence' style described in the
    prompt spec AND plain prose paragraphs (what M2 actually produces) —
    anything that isn't a table row, a CAUSE/SUBCAUSE/EFFECT marker, a
    trace tag, the ID line, a meta field, or the title line itself."""
    out = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if exclude_title and line.strip('"\'') == exclude_title.strip('"\''):
            continue
        if any(re.match(p, line, re.IGNORECASE) for p in _NARRATIVE_SKIP_PATTERNS):
            continue
        out.append(line)
    return out


def _clean_markdown_inline(text: str) -> str:
    """Strip markdown noise (**bold**, `code`) the model tends to add,
    since it's rendered as plain styled text, not interpreted markdown."""
    if not text:
        return text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text


def _parse_llr_block(block: str) -> dict:
    """Parse one LLR sub-block (from 'LLR-SUBSYSTEM-NNN' up to [END_REQ])."""
    llr = {}
    id_match = re.match(r'\s*(LLR-[A-Z]+-\d+(?:-\d+)?)', block)
    llr['ID'] = id_match.group(1) if id_match else '(unparsed ID)'

    # JUS tags may or may not nest a bracket: [JUS.[Rxx] section] (as
    # specified) or [JUS.Rxx section] (as M2 actually produced it) — accept
    # both. COV tags never nest: [COV.HLR-xxx]
    trace_tags = re.findall(
        r'\[(COV\.[^\[\]]+|JUS\.(?:\[[^\]]+\])?[^\]]*)\]', block
    )
    llr['TraceTags'] = [_clean_markdown_inline(t) for t in trace_tags]

    title_match = re.search(
        r'\]\s*\n\s*(["\']?)([A-Za-z][^\n\[]{1,80}?)\1\s*\n', block
    )
    raw_title = title_match.group(2).strip() if title_match else ''
    llr['Title'] = _clean_markdown_inline(raw_title)

    llr['CausesEffects'] = _parse_causes_effects(block)
    llr['Narrative'] = [_clean_markdown_inline(l) for l in _extract_narrative(block, exclude_title=raw_title)]

    meta = _parse_labeled_fields(block, LLR_META_FIELDS)
    # M2 sometimes emits "Traceability:" instead of the specified
    # "Design-Traceability:" — accept it as an alias (negative lookbehind
    # avoids re-matching inside "Design-Traceability:" itself).
    if not meta.get('Design-Traceability'):
        m = re.search(r'(?<!Design-)\bTraceability:\s*(.*?)(?=\n|\Z)', block)
        if m:
            meta['Design-Traceability'] = m.group(1).strip()
    meta['Mean-of-Verification'] = _clean_markdown_inline(meta.get('Mean-of-Verification', ''))
    meta['Rationale'] = _clean_markdown_inline(meta.get('Rationale', ''))
    llr.update(meta)
    return llr


def _normalize_numbered_subheadings(block: str) -> str:
    """Real M2 output sometimes uses numbered markdown sub-headings for
    function fields ("#### IV.1.1.1 Prototype") instead of the plain
    "Prototype: value" colon-field the prompt specifies - this mirrors
    the original gold-standard template's numbering style. Convert any
    "#### <number> <Label>" heading into "<Label>:" so the existing
    colon-field extractor (_parse_labeled_fields) handles both styles
    uniformly, whichever one a given run actually produced."""
    return re.sub(
        r'^#{4}\s+(?:IV\.\d+\.\d+\.\d+\s+)?(.+?)\s*$',
        lambda m: f"{m.group(1).strip()}:",
        block, flags=re.MULTILINE
    )


def _parse_function_block(header_text: str, block: str) -> dict:
    """Parse one function's content. header_text is the text captured from
    a '### function_name()' markdown header when available (preferred,
    matches real M2 output); falls back to extracting the name from the
    Prototype field when parsing a legacy FUNCTION_START/END block instead
    (header_text='' in that case)."""
    block = _normalize_numbered_subheadings(block)
    fn = _parse_labeled_fields(
        block, FUNCTION_FIELDS,
        extra_stop_patterns=[
            r'\n\s*LLR-[A-Z]+-\d+(?:-\d+)?',
            r'\n\s*Data Dictionary Tags\s*:',
            r'\n\s*Requirement Block\s*:',
            r'\n\s*Requirement\s*:',
        ]
    )

    name = ''
    if header_text:
        name = re.sub(r'[\*`]', '', header_text).strip()
        # Strip a leading "IV.1.1 " (or similar) numbering prefix some
        # runs prepend to the function name in the heading itself -
        # without this, the heading renders as "IV.1.1 IV.1.1
        # function_name" once the builder adds its own numbering.
        name = re.sub(r'^IV\.\d+\.\d+\s+', '', name).strip()
        name = re.sub(r'\(\)\s*$', '', name).strip()
    if not name:
        name_match = re.search(r'\bProto(?:type)?:\s*[\w\s\*`]+?\b(\w+)\s*\(', block)
        name = name_match.group(1) if name_match else '(unknown function)'
    fn['Name'] = name

    for f in FUNCTION_FIELDS:
        fn[f] = _clean_markdown_inline(fn.get(f, ''))

    fn['LLRs'] = []
    id_positions = [m.start() for m in re.finditer(r'(?m)^\s*LLR-[A-Z]+-\d+(?:-\d+)?', block)]
    for idx, pos in enumerate(id_positions):
        end = id_positions[idx + 1] if idx + 1 < len(id_positions) else len(block)
        sub_block = block[pos:end]
        fn['LLRs'].append(_parse_llr_block(sub_block))
    return fn


ROMAN_TO_NUM = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}


def _split_sections_roman(text: str) -> list:
    """Split on 'I - ...' / 'II - ...' / ... / 'V - ...' headers (v4.0
    format, mirrors SRD). Longest-alternative-first ordering isn't
    strictly required (the mandatory trailing separator disambiguates
    'I' from 'IV' etc. via backtracking) but is kept for clarity/speed."""
    pattern = re.compile(
        r'(?:\A|\n)\s*#{0,3}\s*(III|IV|II|V|I)\s*[-—:]\s*([^\n]*)\n(.*?)'
        r'(?=(?:\n)\s*#{0,3}\s*(?:III|IV|II|V|I)\s*[-—:]|\Z)',
        re.DOTALL
    )
    return [(ROMAN_TO_NUM[m.group(1)], m.group(3).strip()) for m in pattern.finditer(text)]


def _split_sections_digit(text: str) -> list:
    """Legacy fallback: 'SECTION 1.0 — ...' format (v3.x)."""
    pattern = re.compile(
        r'#{0,3}\s*SECTION\s+(\d)(?:\.0)?\s*[—\-:]\s*([^\n]*)\n(.*?)'
        r'(?=#{0,3}\s*SECTION\s+\d(?:\.0)?\s*[—\-:]|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    return [(int(m.group(1)), m.group(3).strip()) for m in pattern.finditer(text)]


def _parse_m2_output(text: str) -> dict:
    """Parse the full M2 output into the 5-section structure (I-V)."""
    text = _strip_think_tags(text)
    result = {
        'introduction': '', 'architecture': '', 'referenced_docs': '',
        'functions': [], 'summary_table': '', 'subsystem': '',
    }

    sections = _split_sections_roman(text)
    if len(sections) < 3:
        sections = _split_sections_digit(text)  # legacy fallback

    for num, content in sections:
        if num == 1:
            result['introduction'] = content
        elif num == 2:
            result['architecture'] = content
        elif num == 3:
            result['referenced_docs'] = content
        elif num == 4:
            # Function boundaries are level-3 headers ONLY ("### IV.1.1
            # boot_manager_process" or "### function_name()") - NOT
            # level-4 sub-field headers ("#### IV.1.1.1 Prototype"),
            # which a real M2 run now sometimes emits (mirroring the
            # numbered-subsection style of the original gold-standard
            # template). Using #{2,4} here previously treated every
            # sub-field as its own "function", causing duplicated
            # headers and every field reading as empty/None.
            fn_pattern = re.compile(r'^#{3}\s+(.+?)\n(.*?)(?=^#{3}\s+|\Z)',
                                     re.DOTALL | re.MULTILINE)
            fn_matches = list(fn_pattern.finditer(content))
            if fn_matches:
                for fm in fn_matches:
                    result['functions'].append(_parse_function_block(fm.group(1), fm.group(2)))
            else:
                fn_blocks = re.findall(
                    r'---FUNCTION_START---(.*?)---FUNCTION_END---', content, re.DOTALL
                )
                if fn_blocks:
                    for fb in fn_blocks:
                        result['functions'].append(_parse_function_block('', fb))
                else:
                    result['functions'].append({
                        'Name': '(raw — no function headers found)',
                        'Prototype': '', 'Parameters': '', 'Pre-conditions': '',
                        'Called Functions': '', 'Input Data': '', 'Output Data': '',
                        'LLRs': [], '_raw_fallback': content,
                    })
        elif num == 5:
            result['summary_table'] = content

    # Subsystem code, used for the "IV.1 — <SUBSYSTEM> ..." heading —
    # inferred from the first LLR ID found (an SDDD covers one subsystem).
    for fn in result['functions']:
        for llr in fn.get('LLRs', []):
            m = re.match(r'LLR-([A-Z]+)-', llr.get('ID', ''))
            if m:
                result['subsystem'] = m.group(1)
                break
        if result['subsystem']:
            break

    return result


def _extract_dd_tags(text: str) -> dict:
    """Extract [VAR]/[CONST]/[TYPE] Data Dictionary tags from raw M2 text.
    Shared by sddd_builder.py (nothing to render, just kept out of the
    docx) and dd_builder.py (builds DD-xxx.xlsx from this)."""
    text = _strip_think_tags(text)
    dd = {'variables': [], 'constants': [], 'types': []}

    for m in re.finditer(r'\[VAR\]\s*(.+)', text):
        parts = [p.strip() for p in m.group(1).split('|')]
        parts += [''] * (9 - len(parts))
        dd['variables'].append({
            'name': parts[0], 'type': parts[1], 'range': parts[2],
            'description': parts[3], 'unit': parts[4], 'initializer': parts[5],
            'producers': parts[6], 'consumers': parts[7], 'comments': parts[8],
        })

    for m in re.finditer(r'\[CONST\]\s*(.+)', text):
        parts = [p.strip() for p in m.group(1).split('|')]
        parts += [''] * (5 - len(parts))
        dd['constants'].append({
            'name': parts[0], 'type': parts[1], 'definition': parts[2],
            'description': parts[3], 'comments': parts[4],
        })

    for m in re.finditer(r'\[TYPE\]\s*(.+)', text):
        parts = [p.strip() for p in m.group(1).split('|')]
        parts += [''] * (5 - len(parts))
        dd['types'].append({
            'name': parts[0], 'type': parts[1], 'definition': parts[2],
            'description': parts[3], 'comments': parts[4],
        })

    return dd


# ── LLR RENDERING ────────────────────────────────────────────────────────────
def _render_causes_effects_table(doc, rows: list):
    """Render the professional matrix layout: causes become column
    headers (with a merged 'Cause' label spanning them), effects sit in
    a single data row beneath, with a merged 'Effect' row-label on the
    left — this is a straight transpose of the (cause, effect) pairs
    already parsed from M2's reliable 2-column pipe table, no change to
    the parsing/generation format was needed for this."""
    if not rows:
        _add_body(doc, "[Causes/Effects table not found or could not be parsed]")
        return

    n = len(rows)
    tbl = doc.add_table(rows=3, cols=n + 1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    def _style_label_cell(cell, text):
        cell.text = text
        _set_cell_bg(cell, CE_HEADER_BG)
        r = cell.paragraphs[0].runs[0]
        r.bold = True
        r.font.name = FONT_NAME
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _style_data_cell(cell, text, bg=None):
        cell.text = text
        if bg:
            _set_cell_bg(cell, bg)
        r = cell.paragraphs[0].runs[0]
        r.font.name = FONT_NAME
        r.font.size = Pt(9.5)
        r.font.color.rgb = BLACK
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Row 0: blank corner + merged "Cause" spanning all condition columns
    tbl.cell(0, 0).text = ''
    for j in range(1, n + 1):
        tbl.cell(0, j).text = ''
    if n >= 1:
        merged = tbl.cell(0, 1)
        if n > 1:
            merged = merged.merge(tbl.cell(0, n))
        _style_label_cell(merged, "Cause")

    # Row 1 (cause values) + Row 2 (effect values), col 0 = merged "Effect" label
    effect_label = tbl.cell(1, 0).merge(tbl.cell(2, 0))
    _style_label_cell(effect_label, "Effect")

    for j, row_data in enumerate(rows, start=1):
        cause_text = row_data['cause'] if row_data['cause'] not in ('', '-') else 'Unconditional'
        effect_text = row_data['effect'] or 'No effect'
        _style_data_cell(tbl.cell(1, j), cause_text, bg=CAUSE_BG)
        _style_data_cell(tbl.cell(2, j), effect_text)

    doc.add_paragraph()


def _add_field_subheading(doc, text, italic=True, color=None):
    """Exact style-map match for the numbered field sub-headings inside a
    function/LLR block (Prototype, Parameters, ..., Causes/Effects,
    Implementation): Arial 10pt bold, italic + black by default, except
    'Requirement' which is bold NON-italic DARK_TITLE (#1c1c1c) — this is
    a different style tier from the top-level Section/function headings,
    do not reuse _add_heading(level=3) for these."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.italic = italic
    run.font.name = FONT_NAME
    run.font.size = Pt(10)
    run.font.color.rgb = color if color is not None else BLACK
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(3)
    return p


def _render_llr(doc, llr: dict, prefix: str = ""):
    _add_id_heading(doc, llr['ID'])
    for tag in llr.get('TraceTags', []):
        color = JUS_GREEN if tag.upper().startswith('JUS.') else COV_BLUE
        _add_italic_blue(doc, f"[{tag}]", color=color)
    _add_horizontal_rule(doc)

    _add_field_subheading(doc, "Causes / Effects")
    _render_causes_effects_table(doc, llr.get('CausesEffects', []))

    if llr.get('Narrative'):
        # bracketed-label lines ("[X]: ...") -> "Implementation" (template
        # format); plain prose -> "Narrative" (backward-compat fallback).
        is_bracketed = all(re.match(r'^\[.+?\]\s*:', l) for l in llr['Narrative'])
        _add_field_subheading(doc, "Implementation" if is_bracketed else "Narrative")
        for line in llr['Narrative']:
            _add_body(doc, line)

    trace_val = llr.get('Design-Traceability', '')
    meta_pairs = [
        ("Design-Traceability", trace_val, None),
        ("Mean-of-Verification", llr.get('Mean-of-Verification', ''), None),
        ("Rationale", llr.get('Rationale', ''), None),
    ]
    _add_borderless_field_list(doc, meta_pairs)

    _add_horizontal_rule(doc)
    _add_italic_blue(doc, "[END_REQ]", color=ID_BLUE)
    doc.add_paragraph()


def _add_io_bullets(doc, raw_value: str):
    """Render Input/Output Data as IN:/OUT:/INOUT: bullets with a bold-
    italic label followed by an italic value, per the style map. Falls
    back to generic bullet rendering if the IN:/OUT:/INOUT: labels
    aren't present (older/simpler model output)."""
    lines = [l.strip() for l in raw_value.split('\n') if l.strip()]
    lines = [l.lstrip('-• ').strip() for l in lines]
    has_labels = any(re.match(r'(IN|OUT|INOUT)\s*:', l, re.IGNORECASE) for l in lines)
    if not has_labels:
        _render_multiline_field(doc, raw_value)
        return
    for line in lines:
        m = re.match(r'(IN|OUT|INOUT)\s*:\s*(.*)$', line, re.IGNORECASE)
        p = doc.add_paragraph(style='List Bullet')
        if m:
            label_run = p.add_run(f"{m.group(1).upper()}: ")
            label_run.bold = True
            label_run.italic = True
            label_run.font.name = FONT_NAME
            label_run.font.size = Pt(10)
            value_run = p.add_run(_clean_markdown_inline(m.group(2).strip() or 'None'))
            value_run.italic = True
            value_run.font.name = FONT_NAME
            value_run.font.size = Pt(10)
        else:
            r = p.add_run(_clean_markdown_inline(line))
            r.italic = True
            r.font.name = FONT_NAME
            r.font.size = Pt(10)


def _render_function(doc, fn: dict, prefix: str = ""):
    heading = f"{prefix} {fn['Name']}()" if prefix else f"{fn['Name']}()"
    p = doc.add_paragraph()
    run = p.add_run(heading)
    run.bold = True
    run.font.name = FONT_NAME
    run.font.size = Pt(13)
    run.font.color.rgb = MID_BLUE
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(6)

    def _sub_heading(n, label, italic=True, color=None):
        text = f"{prefix}.{n} {label}" if prefix else label
        _add_field_subheading(doc, text, italic=italic, color=color)

    # .1 Prototype
    _sub_heading(1, "Prototype")
    proto = fn.get('Prototype', '')
    if proto:
        pp = doc.add_paragraph()
        pp.paragraph_format.left_indent = Cm(1)
        r = pp.add_run(proto)
        r.font.name = FONT_NAME
        r.font.size = Pt(10)
    else:
        _add_body(doc, "None")

    # .2 Parameters — real table if M2 emitted a pipe table, else fallback
    _sub_heading(2, "Parameters")
    params_val = fn.get('Parameters', '')
    param_lines = [l for l in params_val.split('\n') if l.strip().startswith('|')]
    if len(param_lines) >= 2:
        _add_pipe_table(doc, param_lines)
    elif params_val and params_val.strip().lower() not in ('none', ''):
        _render_multiline_field(doc, params_val)
    else:
        _add_body(doc, "None")

    # .3 Pre-conditions / .4 Called Functions
    _sub_heading(3, "Pre-conditions")
    val = fn.get('Pre-conditions', '')
    _render_multiline_field(doc, val) if val and val.strip().lower() not in ('none', '') else _add_body(doc, "None")

    _sub_heading(4, "Called Functions")
    val = fn.get('Called Functions', '')
    _render_multiline_field(doc, val) if val and val.strip().lower() not in ('none', '') else _add_body(doc, "None")

    # .5 Input Data / .6 Output Data — IN/OUT/INOUT bullets
    _sub_heading(5, "Input Data")
    val = fn.get('Input Data', '')
    _add_io_bullets(doc, val) if val.strip() else _add_body(doc, "None")

    _sub_heading(6, "Output Data")
    val = fn.get('Output Data', '')
    _add_io_bullets(doc, val) if val.strip() else _add_body(doc, "None")

    if fn.get('_raw_fallback'):
        _add_body(doc, "[Structured function headers not found — raw model output below]")
        for line in fn['_raw_fallback'].split('\n')[:200]:
            if line.strip():
                _add_body(doc, line.strip())
        return

    # .7 Requirement — one shared numbered heading, may contain several
    # LLR blocks (each carries its own -01/-02 ID suffix).
    if fn.get('LLRs'):
        _sub_heading(7, "Requirement", italic=False, color=DARK_TITLE)
        for llr in fn['LLRs']:
            _render_llr(doc, llr, prefix=prefix)


def _extract_doc_id(introduction_text: str, version: str) -> str:
    """Compute the Document ID purely from the pipeline-supplied version
    string - never search M2's own raw text for a self-assigned
    "Document ID: SDDD-xxx" line, since M2 is not supposed to assign one
    (baseline/minor tracking is the database's job, not the model's).
    Format matches the project's unified convention: bare "SDDD-{baseline}"
    when minor is 0 (i.e. this could be a baseline), "SDDD-{baseline}.{minor}"
    otherwise - never zero-padded (SDDD-1, not SDDD-001)."""
    try:
        baseline_str, _, minor_str = str(version).partition('.')
        baseline = int(baseline_str)
        minor = int(minor_str) if minor_str else 0
        return f"SDDD-{baseline}" if minor == 0 else f"SDDD-{baseline}.{minor}"
    except (ValueError, TypeError):
        return "SDDD-1"


# ── MAIN BUILDER ─────────────────────────────────────────────────────────────
def build_sddd(m2_output: str, output_path: str, version: str = "1.0",
               project: str = "I-SCEET") -> str:
    """Build SDDD-0xx.docx from M2 v4.0 text output (I-V structure,
    mirrors SRD numbering). See module docstring for the expected format.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    parsed = _parse_m2_output(m2_output)
    doc_id = _extract_doc_id(parsed['introduction'], version)
    subsystem = parsed.get('subsystem') or '???'

    doc = Document()
    section = doc.sections[0]
    section.page_width  = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2)

    _make_cover(doc, doc_id, "SOFTWARE DESIGN DESCRIPTION DOCUMENT",
                version, project, "M2 (I-SCEET — Mistral Small 24B)", date_str, "A")
    _add_header_footer(doc, doc_id, version, date_str)
    _make_revision_table(doc, version, date_str, generator="M2 (I-SCEET AI)")
    doc.add_page_break()

    # I — Introduction
    _add_heading(doc, "I - INTRODUCTION", 1)
    if parsed['introduction']:
        _render_multiline_field(doc, parsed['introduction'])
    else:
        _add_body(doc, "[Section I not found in model output]")
    doc.add_page_break()

    # II — Architecture
    _add_heading(doc, "II - ARCHITECTURE", 1)
    if parsed['architecture']:
        _render_multiline_field(doc, parsed['architecture'], allow_subheadings=True)
    else:
        _add_body(doc, "[Section II not found in model output]")
    doc.add_page_break()

    # III — Referenced Documents
    _add_heading(doc, "III - REFERENCED DOCUMENTS", 1)
    if parsed['referenced_docs']:
        lines = [l for l in parsed['referenced_docs'].split('\n') if l.strip()]
        if not _add_pipe_table(doc, lines):
            for l in lines:
                _add_body(doc, l.strip())
    else:
        _add_body(doc, "[Section III not found in model output]")
    doc.add_page_break()

    # IV — Requirements (IV.1 subsystem / IV.1.n function / IV.1.n.m LLR)
    _add_heading(doc, "IV - REQUIREMENTS", 1)
    if parsed['functions']:
        _add_heading(doc, f"IV.1 — {subsystem} Low-Level Requirements", 1)
        total_llrs = 0
        for fn_idx, fn in enumerate(parsed['functions'], 1):
            _render_function(doc, fn, prefix=f"IV.1.{fn_idx}")
            total_llrs += len(fn.get('LLRs', []))
        _add_body(doc, f"Total functions: {len(parsed['functions'])}   |   Total LLRs generated: {total_llrs}")
    else:
        _add_body(doc, "[No functions could be parsed from model output]")
    doc.add_page_break()

    # V — Summary (LLR <-> HLR relationship table)
    _add_heading(doc, "V - SUMMARY", 1)
    if parsed['summary_table']:
        lines = [l for l in parsed['summary_table'].split('\n') if l.strip()]
        if not _add_pipe_table(doc, lines):
            for l in lines:
                _add_body(doc, l.strip())
    else:
        # Auto-consolidate LLR<->HLR from parsed COV tags if M2 didn't
        # explicitly emit Section V (defensive — never leave it blank).
        rows = []
        for fn in parsed['functions']:
            for llr in fn.get('LLRs', []):
                hlr_ids = [t.split('.', 1)[1] for t in llr.get('TraceTags', [])
                           if t.startswith('COV.')]
                rows.append((llr['ID'], ', '.join(hlr_ids) or '-',
                             llr.get('Design-Traceability', '')))
        if rows:
            _add_body(doc, "(Auto-consolidated from Section IV — Section V was not explicitly emitted by the model)")
            tbl = doc.add_table(rows=1, cols=3)
            for j, h in enumerate(["LLR ID", "HLR ID(s)", "Traceability"]):
                cell = tbl.rows[0].cells[j]
                cell.text = h
                _set_cell_bg(cell, "1F3864")
                r = cell.paragraphs[0].runs[0]
                r.bold = True
                r.font.color.rgb = WHITE
                r.font.name = FONT_NAME
                r.font.size = Pt(9.5)
            for llr_id, hlr_ids, trace in rows:
                row = tbl.add_row()
                row.cells[0].text = llr_id
                row.cells[1].text = hlr_ids
                row.cells[2].text = trace
                for c in row.cells:
                    if c.paragraphs[0].runs:
                        c.paragraphs[0].runs[0].font.size = Pt(9.5)
                        c.paragraphs[0].runs[0].font.name = FONT_NAME
        else:
            _add_body(doc, "None identified for this subsystem.")

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    doc.save(output_path)
    return output_path


if __name__ == "__main__":
    import sys as _sys

    if len(_sys.argv) < 2:
        print("Usage: python3 sddd_builder.py <texte_brut.txt> [version] [output.docx]")
        print("Exemple: python3 sddd_builder.py SDDD_stm32f303_boot_drv.txt 1.0 sddd_test.docx")
        _sys.exit(1)

    _input_path = _sys.argv[1]
    _version = _sys.argv[2] if len(_sys.argv) > 2 else "1.0"
    _output_path = _sys.argv[3] if len(_sys.argv) > 3 else "SDDD_test.docx"

    if not os.path.exists(_input_path):
        print(f"❌ Fichier introuvable: {_input_path}")
        _sys.exit(1)

    _text = open(_input_path, encoding="utf-8").read()
    print(f"📄 Texte brut lu: {len(_text)} caractères (~{len(_text)//4} tokens)")

    try:
        build_sddd(_text, _output_path, version=_version, project="I-SCEET")
    except Exception as e:
        print(f"❌ ERREUR pendant la génération: {e}")
        import traceback
        traceback.print_exc()
        _sys.exit(1)

    print(f"✅ Document généré: {_output_path}")

    # Diagnostic rapide intégré
    _d = Document(_output_path)
    _count_dup = sum(1 for p in _d.paragraphs if re.match(r'(IV\.\d+\.\d+) \1', p.text))
    _count_notfound = sum(1 for p in _d.paragraphs if 'could not be parsed' in p.text)
    _count_narrative = sum(1 for p in _d.paragraphs if p.text.strip() == 'Narrative')
    _count_dd_leak = sum(1 for p in _d.paragraphs if 'Data Dictionary' in p.text)
    _count_functions = sum(1 for p in _d.paragraphs if re.match(r'^IV\.\d+\.\d+\s+\w+\(\)', p.text.strip()))
    _count_llr = sum(1 for p in _d.paragraphs if re.match(r'^LLR-[A-Z]+-\d+', p.text.strip()))

    print()
    print("=" * 60)
    print("DIAGNOSTIC")
    print("=" * 60)
    print(f"{'❌' if _count_dup else '✅'} En-têtes de fonction dupliqués: {_count_dup}")
    print(f"{'❌' if _count_notfound else '✅'} Causes/Effets non trouvées: {_count_notfound}")
    print(f"{'❌' if _count_narrative else '✅'} Sections 'Narrative' (devrait être 0): {_count_narrative}")
    print(f"{'❌' if _count_dd_leak else '✅'} 'Data Dictionary Tags' qui fuit: {_count_dd_leak}")
    print(f"ℹ️  Fonctions détectées: {_count_functions}")
    print(f"ℹ️  LLR détectées: {_count_llr}")
    print(f"ℹ️  Tables dans le document: {len(_d.tables)}")
    print()
    if _count_dup == 0 and _count_notfound == 0 and _count_narrative == 0 and _count_dd_leak == 0:
        print("🎉 Aucun bug connu détecté.")
    else:
        print("⚠️  Des problèmes ont été détectés — voir le détail ci-dessus.")