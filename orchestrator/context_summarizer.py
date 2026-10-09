"""
================================================================================
 I-SCEET — Context Summarizer (content-preserving, not tag-only)
 File: orchestrator/context_summarizer.py
 Copyright (c) 2026 Hatem Adouani — MIT License
================================================================================
 Unlike tag_extractor.py (pure ID correlation for M6, which only needs to
 know what links to what), M2 needs the actual substance of each HLR - its
 "shall" statement, category, safety effect - to derive meaningful LLRs,
 plus the architecture section for context. This module condenses SRD
 down to that substance, dropping cover-page metadata, the referenced-
 documents list, and per-HLR fields M2 doesn't need (Activation Period,
 Input/Output Data tables, Verification Method, Security Assurance Level,
 Context, Priority, Status) - deterministic regex extraction, not an LLM
 summarization pass.
================================================================================
"""

import re


def _strip_think_tags(text: str) -> str:
    if not text:
        return text
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return re.sub(r'</?think>', '', text).strip()


def _extract_section(text: str, start_marker: str, end_markers: list) -> str:
    if end_markers:
        end_pattern = '|'.join(re.escape(m) for m in end_markers)
        pattern = rf'{re.escape(start_marker)}(.*?)(?:{end_pattern}|\Z)'
    else:
        pattern = rf'{re.escape(start_marker)}(.*)\Z'
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else ''


def extract_hlr_essentials(srd_text: str) -> list:
    """One entry per HLR: ID, Title, Statement, Parent, Upwards
    Traceability, Category, Safety Effect, Rationale - drops the rest."""
    srd_text = _strip_think_tags(srd_text)
    hlrs = []
    for block in re.split(r'\[END_HLR-[\w-]+\]', srd_text)[:-1]:
        m_id = re.search(r'ID:\s*([^\n]+)', block)
        if not m_id:
            continue
        def field(name):
            fm = re.search(rf'{name}:\s*(.+?)(?=\n\s*[A-Z][\w ]*:|\Z)', block, re.DOTALL)
            return fm.group(1).strip() if fm else ''
        hlrs.append({
            "id": m_id.group(1).strip(),
            "title": field("Title"),
            "statement": field("Statement"),
            "parent": field("Parent"),
            "traceability": field("Upwards Traceability"),
            "category": field("Category"),
            "safety_effect": field("Safety Effect"),
            "rationale": field("Rationale"),
        })
    return hlrs


def summarize_sddd_for_m3(sddd_text: str) -> str:
    """Condensed SDDD for M3: reuses sddd_builder.py's own (already
    tested) parser to get a clean structured representation, then
    re-serializes only what M3 needs to generate code - Prototype,
    Parameters, Called Functions, Input/Output Data, the Causes/Effects
    table, and Implementation lines, plus the [VAR]/[TYPE]/[CONST] data
    dictionary tags (needed for correct types/ranges in the code).
    Drops: Section I (Introduction), Section III (References), Section V
    (Summary), and per-LLR Design-Traceability/Mean-of-Verification/
    Rationale - none of that affects what code should be written, only
    why/how it was verified, which is M4/M5/M6's concern, not M3's."""
    import sddd_builder as _sb

    sddd_text = _strip_think_tags(sddd_text)
    parsed = _sb._parse_m2_output(sddd_text)

    lines = ["=== SDDD SUMMARY FOR M3 ===",
             "(condensed via sddd_builder's own parser - Prototype/"
             "Parameters/Causes-Effects/Implementation/DD tags kept in "
             "full; Design-Traceability/Mean-of-Verification/Rationale "
             "and document-level Intro/References/Summary dropped)", ""]

    arch = parsed.get('architecture', '')
    if arch:
        lines.append("--- ARCHITECTURE (Static + Dynamic) ---")
        lines.append(arch.strip()[:2000])
        lines.append("")

    lines.append(f"--- FUNCTIONS ({len(parsed.get('functions', []))} found) ---")
    for fn in parsed.get('functions', []):
        lines.append(f"\n### {fn.get('Name', '?')}()")
        if fn.get('Prototype'):
            lines.append(f"Prototype: {fn['Prototype']}")
        if fn.get('Parameters'):
            lines.append(f"Parameters: {fn['Parameters']}")
        if fn.get('Called Functions'):
            lines.append(f"Called Functions: {fn['Called Functions']}")
        if fn.get('Input Data'):
            lines.append(f"Input Data: {fn['Input Data']}")
        if fn.get('Output Data'):
            lines.append(f"Output Data: {fn['Output Data']}")

        for llr in fn.get('LLRs', []):
            lines.append(f"\n  {llr.get('ID', '?')}")
            for tag in llr.get('TraceTags', []):
                lines.append(f"  [{tag}]")
            if llr.get('Title'):
                lines.append(f"  \"{llr['Title']}\"")
            lines.append("  Causes/Effects:")
            for ce in llr.get('CausesEffects', []):
                lines.append(f"    Cause: {ce.get('cause', '')} -> Effect: {ce.get('effect', '')}")
            if llr.get('Narrative'):
                lines.append("  Implementation:")
                for nline in llr['Narrative']:
                    lines.append(f"    {nline}")

    dd_tags = re.findall(r'\[(?:VAR|CONST|TYPE)\][^\n]+', sddd_text)
    if dd_tags:
        lines.append(f"\n--- DATA DICTIONARY TAGS ({len(dd_tags)} found) ---")
        lines.extend(dd_tags)

    return "\n".join(lines)


def summarize_srd_for_m2(srd_text: str) -> str:
    """Condensed SRD: Section III (Architecture) kept close to verbatim
    (already compact/tabular), Section IV reduced to per-HLR essentials,
    Section V (PDS<->HLR summary) kept as-is. Cover page, Section I
    (Introduction), Section II (Referenced Documents) dropped entirely -
    M2 doesn't need certification-context prose or a reference list, only
    what it must design against."""
    srd_text = _strip_think_tags(srd_text)

    arch_section = _extract_section(
        srd_text, "SECTION III", ["SECTION IV", "SECTION V"]
    )
    summary_section = _extract_section(
        srd_text, "SECTION V", []
    )
    hlrs = extract_hlr_essentials(srd_text)

    lines = ["=== SRD SUMMARY FOR M2 ===",
             "(condensed - full HLR statements and architecture kept, "
             "metadata/cover-page/references dropped)", ""]

    if arch_section:
        lines.append("--- SECTION III: SYSTEM ARCHITECTURE ---")
        lines.append(arch_section.strip())
        lines.append("")

    lines.append(f"--- SECTION IV: HLRs ({len(hlrs)} found) ---")
    for h in hlrs:
        lines.append(f"\n{h['id']} — {h['title']}")
        lines.append(f"Statement: {h['statement']}")
        lines.append(f"Parent: {h['parent']} | Traceability: {h['traceability']} | "
                     f"Category: {h['category']} | Safety Effect: {h['safety_effect']}")
        if h['rationale'] and h['rationale'] != '-':
            lines.append(f"Rationale: {h['rationale']}")

    if summary_section:
        lines.append("\n--- SECTION V: SUMMARY ---")
        lines.append(summary_section.strip())

    return "\n".join(lines)
