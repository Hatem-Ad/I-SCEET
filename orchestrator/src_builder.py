"""
================================================================================
 I-SCEET — SRC Builder v1.1
 File: orchestrator/src_builder.py
 Copyright (c) 2026 Hatem Adouani — MIT License
================================================================================
 Parses M3 raw text into a source-code ZIP. M3's actual deployed prompt
 (models/system_prompts/M3_system_prompt.txt — "v2.0 PROFESSIONAL") emits:

 === FILE: /src/clk_driver/LLR-CLK-001-01.c ===
 ...content...

 === FILE: /src/clk_driver/clk_driver.h ===
 ...content...

 v1.1 fix: the regex previously only matched a DIFFERENT, never-actually-
 used "---FILE_START:---/---FILE_END---" format, so every real M3 run
 matched ZERO files and silently fell through to the LEGACY_src.txt
 fallback - the ZIP was structurally empty every time. Now matches the
 real "=== FILE: path ===" marker (case-insensitive on the word FILE),
 with the old marker kept as a secondary pattern in case some other M3
 lineage still emits it.

 The builder creates the requested tree, writes a MANIFEST.txt, and packages
 it as SRC_vX.Y.zip.
================================================================================
"""

import os
import re
import zipfile
from pathlib import Path


# Real M3 format (primary): "=== FILE: path ===" then content, until the
# next "=== FILE:" marker or end of string.
FILE_BLOCK_RE = re.compile(
    r"===\s*FILE:\s*([^\n\r=]+?)\s*===\s*\n(.*?)(?=\n===\s*FILE:|\Z)",
    re.DOTALL | re.IGNORECASE,
)

# Legacy/alternate format, kept as a fallback in case a different M3
# lineage or an older cached output uses it.
LEGACY_FILE_BLOCK_RE = re.compile(
    r"---FILE_START:\s*([^\n\r]+?)\s*---\s*\n(.*?)(?:\n\s*---FILE_END---|\Z)",
    re.DOTALL | re.IGNORECASE,
)


def _strip_think_tags(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return re.sub(r"</?think>", "", text).strip()


def _strip_code_fences(content: str) -> str:
    """M3 sometimes wraps file content in ```c ... ``` fences even though
    the prompt says not to add commentary - strip a single leading/
    trailing fence if present, rather than shipping the fence markers
    into the actual source file."""
    content = content.strip()
    content = re.sub(r"^```[a-zA-Z]*\n", "", content)
    content = re.sub(r"\n```\s*$", "", content)
    return content


def _safe_relpath(raw_path: str) -> str:
    """Normalize and constrain generated paths to the ZIP root."""
    raw_path = raw_path.strip().replace("\\", "/")
    raw_path = raw_path.lstrip("/")
    if raw_path.startswith("src/"):
        raw_path = raw_path[len("src/"):]
    parts = []
    for part in raw_path.split("/"):
        part = part.strip()
        if not part or part in {".", ".."}:
            continue
        parts.append(part)
    rel = "/".join(parts)
    if not rel:
        raise ValueError(f"Invalid generated path: {raw_path!r}")
    return rel


def parse_src_files(text_output: str) -> dict:
    """Return {relative_path: file_content} parsed from M3 file blocks."""
    text_output = _strip_think_tags(text_output or "")
    files = {}

    for match in FILE_BLOCK_RE.finditer(text_output):
        rel = _safe_relpath(match.group(1))
        content = _strip_code_fences(match.group(2)) + "\n"
        files[rel] = content

    if not files:
        for match in LEGACY_FILE_BLOCK_RE.finditer(text_output):
            rel = _safe_relpath(match.group(1))
            content = _strip_code_fences(match.group(2)) + "\n"
            files[rel] = content

    # Last-resort fallback for genuinely unmarked output: preserve it
    # instead of losing content, but this should not happen in practice
    # once the marker format matches the real M3 prompt.
    if not files and text_output.strip():
        files["LEGACY_src.txt"] = text_output.strip() + "\n"
    return files


def build_src(text_output: str, output_zip_path: str, version: str = "1.0") -> str:
    """Build SRC_vX.Y.zip from M3 text output."""
    files = parse_src_files(text_output)
    output_zip = Path(output_zip_path)
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    manifest_lines = [
        "I-SCEET M3 Source Code Manifest",
        f"Version: {version}",
        f"Generated files: {len(files)}",
        "",
    ]
    manifest_lines.extend(f"- {path}" for path in sorted(files))
    manifest = "\n".join(manifest_lines) + "\n"

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("MANIFEST.txt", manifest)
        for rel, content in sorted(files.items()):
            zf.writestr(rel, content)

    return str(output_zip)