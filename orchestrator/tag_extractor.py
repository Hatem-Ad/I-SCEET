"""
================================================================================
 I-SCEET — Tag Extractor for M6
 File: orchestrator/tag_extractor.py
 Copyright (c) 2026 Hatem Adouani — MIT License
================================================================================
 Pre-processes M6's inputs deterministically: instead of feeding M6 the
 full raw text of SRD + SDDD + /src + SUTC + SVTC (which can exceed
 context limits on larger projects), this script mechanically extracts
 just the ID-correlation tags each document already carries, and produces
 a compact structured summary. M6 then only has to correlate IDs already
 laid out for it, instead of scanning full documents for tags itself.

 This is regex-based extraction, not LLM summarization - deterministic,
 free of token cost, and scales to any project size.
================================================================================
"""

import re


def _strip_think_tags(text: str) -> str:
    if not text:
        return text
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return re.sub(r'</?think>', '', text).strip()


def extract_hlr_tags(srd_text: str) -> list:
    """From SRD: each HLR's ID + Parent field."""
    srd_text = _strip_think_tags(srd_text)
    results = []
    for m in re.finditer(
        r'ID:\s*(HLR-[\w-]+)\s*\n.*?Parent:\s*(\S[^\n]*)',
        srd_text, re.DOTALL
    ):
        hlr_id, parent = m.group(1).strip(), m.group(2).strip()
        results.append({"hlr_id": hlr_id, "parent": parent})
    return results


def extract_llr_tags(sddd_text: str) -> list:
    """From SDDD: each LLR's ID + [COV.HLR-xxx] tag."""
    sddd_text = _strip_think_tags(sddd_text)
    results = []
    for m in re.finditer(
        r'(LLR-[\w-]+)\s*\n\s*\[COV\.(HLR-[\w-]+)\]',
        sddd_text
    ):
        llr_id, hlr_id = m.group(1).strip(), m.group(2).strip()
        results.append({"llr_id": llr_id, "cov_hlr": hlr_id})
    return results


def extract_code_tags(src_text: str) -> list:
    """From /src (concatenated file contents or a single file): each
    function's name + @req tag(s). Looks for the standard I-SCEET file
    header pattern used by M3."""
    src_text = _strip_think_tags(src_text)
    results = []
    # @req line, followed shortly by the function signature it documents
    for m in re.finditer(
        r'@req\s+([\w,\-\s]+?)\s*\n(?:[^\n]*\n){0,6}?\s*'
        r'(?:[\w_]+\s+)+?([\w_]+)\s*\(',
        src_text
    ):
        req_ids = [r.strip() for r in m.group(1).split(',') if r.strip()]
        func_name = m.group(2).strip()
        results.append({"function": func_name, "req_ids": req_ids})
    return results


def extract_sutc_tags(sutc_text: str) -> list:
    """From SUTC: each function block's LLR-ID(s) + the UFT-IDs inside it."""
    sutc_text = _strip_think_tags(sutc_text)
    results = []
    block_pattern = re.compile(
        r'#{2,3}\s+([\w_]+)\(\)[ \t]*[—-][ \t]*([^\n]+?)[ \t]*\n'
        r'(.*?)(?=#{2,3}\s+[\w_]+\(\)|\Z)',
        re.DOTALL
    )
    for bm in block_pattern.finditer(sutc_text):
        func_name = bm.group(1).strip()
        llr_ids = [x.strip() for x in bm.group(2).split(',') if x.strip()]
        body = bm.group(3)
        uft_ids = sorted(set(re.findall(r'SUTC_[A-Z0-9]+_UFT\d+', body)))
        results.append({"function": func_name, "llr_ids": llr_ids, "uft_ids": uft_ids})
    return results


def extract_svtc_tags(svtc_text: str) -> list:
    """From SVTC: each capability block's HLR-ID(s) + the FT-IDs inside it."""
    svtc_text = _strip_think_tags(svtc_text)
    results = []
    block_pattern = re.compile(
        r'#{2,3}\s+([^\n]+?)[ \t]*[—-][ \t]*(HLR[^\n]+?)[ \t]*\n'
        r'(.*?)(?=#{2,3}\s+[^\n]+?[—-][ \t]*HLR|\Z)',
        re.DOTALL
    )
    for bm in block_pattern.finditer(svtc_text):
        capability = bm.group(1).strip()
        hlr_ids = [x.strip() for x in bm.group(2).split(',') if x.strip()]
        body = bm.group(3)
        ft_ids = sorted(set(re.findall(r'SVTC_[A-Z0-9]+_FT\d+', body)))
        results.append({"capability": capability, "hlr_ids": hlr_ids, "ft_ids": ft_ids})
    return results


def build_m6_input(srd_text: str = "", sddd_text: str = "", src_text: str = "",
                    sutc_text: str = "", svtc_text: str = "") -> str:
    """Build the compact tag-correlation summary that replaces raw
    document text as M6's actual input."""
    lines = ["=== TAG EXTRACTION SUMMARY FOR M6 ===",
             "(mechanically extracted - not narrative; correlate these "
             "IDs directly, no need to search source documents)", ""]

    if srd_text:
        hlrs = extract_hlr_tags(srd_text)
        lines.append(f"[SRD - HLRs] ({len(hlrs)} found)")
        for h in hlrs:
            lines.append(f"{h['hlr_id']} | Parent: {h['parent']}")
        lines.append("")

    if sddd_text:
        llrs = extract_llr_tags(sddd_text)
        lines.append(f"[SDDD - LLRs] ({len(llrs)} found)")
        for l in llrs:
            lines.append(f"{l['llr_id']} | COV: {l['cov_hlr']}")
        lines.append("")

    if src_text:
        funcs = extract_code_tags(src_text)
        lines.append(f"[/src - Functions] ({len(funcs)} found)")
        for f in funcs:
            lines.append(f"{f['function']} | @req: {', '.join(f['req_ids'])}")
        lines.append("")

    if sutc_text:
        sutc_blocks = extract_sutc_tags(sutc_text)
        total_uft = sum(len(b['uft_ids']) for b in sutc_blocks)
        lines.append(f"[SUTC - Unit Test Cases] ({len(sutc_blocks)} functions, {total_uft} UFT cases)")
        for b in sutc_blocks:
            lines.append(f"{b['function']}() -> {', '.join(b['llr_ids'])} | "
                         f"UFT-IDs: {', '.join(b['uft_ids'])}")
        lines.append("")

    if svtc_text:
        svtc_blocks = extract_svtc_tags(svtc_text)
        total_ft = sum(len(b['ft_ids']) for b in svtc_blocks)
        lines.append(f"[SVTC - Functional Test Cases] ({len(svtc_blocks)} capabilities, {total_ft} FT cases)")
        for b in svtc_blocks:
            lines.append(f"{b['capability']} -> {', '.join(b['hlr_ids'])} | "
                         f"FT-IDs: {', '.join(b['ft_ids'])}")
        lines.append("")

    return "\n".join(lines)
