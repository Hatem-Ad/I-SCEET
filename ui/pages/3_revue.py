"""
================================================================================
 I-SCEET — Page 3 : Revue globale
 File: ui/pages/3_revue.py
================================================================================
 v2: fixed a real bug - the old dict comprehension {a["module"]: a for a in
 artifacts} silently kept only the LAST artifact per module, so once M2
 started producing 3 artifacts (SDDD, DD, CT) only one of them ever showed
 up. Now groups by module -> list of artifacts, and DD/CT (xlsx, content="")
 get a spreadsheet preview read from file_path instead of an empty text box.
 Names updated: SVCP-LLT-001/SVCP-HLT-001 -> SUTC, STD-001 -> TM.
================================================================================
"""

import streamlit as st
import sys, os
import difflib

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from Backend.db import (get_artifacts, save_review, get_reviews,
                        get_artifact_history, baseline_artifact)

st.set_page_config(page_title="Revue — I-SCEET", page_icon="🔍", layout="wide")
st.title("🔍 Revue globale des artefacts")
st.divider()

active = st.session_state.get("active_project")
if not active:
    st.warning("⚠️ No active project. Go to **1 Upload** first.")
    st.stop()

st.markdown(f"**Project:** {active['name']} — DAL {active['dal_level']}")
st.divider()

artifacts = get_artifacts(active["id"])

# Group by module -> {type: artifact}, keeping the latest version of each type
by_module = {}
for a in artifacts:
    if a["module"] not in ["M1", "M2", "M3", "M4", "M5", "M6"]:
        continue
    by_module.setdefault(a["module"], {})
    existing = by_module[a["module"]].get(a["type"])
    if existing is None or a.get("version", 0) >= existing.get("version", 0):
        by_module[a["module"]][a["type"]] = a

if not by_module:
    st.info("⬜ No artifacts yet. Run the pipeline on **2 Pipeline** first.")
    st.stop()

existing_reviews = {r["module"]: r for r in get_reviews(active["id"])}

MODULE_INFO = {
    "M1": ("📋 High Level Requirements",              ["SRD"]),
    "M2": ("📐 Low Level Requirements + Architecture", ["SDDD", "DD", "CT"]),
    "M3": ("💻 Source Code C",                         ["/src"]),
    "M4": ("🧪 Low Level Tests",                       ["SUTC"]),
    "M5": ("🧪 High Level Tests",                      ["SVTC"]),
    "M6": ("🗺️ Traceability Matrix",                   ["TM"]),
}

# ── SUMMARY BAR ───────────────────────────────────────────────────────────────
reviews = get_reviews(active["id"])
c1, c2, c3, c4 = st.columns(4)
c1.metric("Modules generated", f"{len(by_module)}/6")
c2.metric("✅ Approved",  sum(1 for r in reviews if r["status"] == "approved"))
c3.metric("⚠️ Revision",  sum(1 for r in reviews if r["status"] == "needs_revision"))
c4.metric("❌ Rejected",  sum(1 for r in reviews if r["status"] == "rejected"))

st.divider()


def render_baseline_section(artifact, project_id, module_id):
    """🔒 Baseline button, with a Beyond-Compare-style diff against the
    previous version shown before the user confirms - so a baseline is
    never locked in blind."""
    st.divider()
    st.markdown("**🔒 Baseline this artifact**")

    if artifact["status"] == "BASELINE":
        st.info(
            f"This is already a BASELINE (v{artifact['version']}, "
            f"baselined {artifact.get('baselined_at', '')[:16]} by "
            f"{artifact.get('baselined_by', '—')}). "
            f"Generate a new draft to continue working."
        )
        return

    st.caption(f"Current draft: v{artifact['version']} (DRAFT)")

    confirm_key = f"confirm_baseline_{artifact['id']}"
    show_key = f"show_diff_{artifact['id']}"

    if not st.session_state.get(show_key):
        if st.button("🔒 Baseline this version", key=f"start_baseline_{artifact['id']}"):
            st.session_state[show_key] = True
            st.rerun()
        return

    # ── DIFF VIEW ────────────────────────────────────────────────────────────
    history = get_artifact_history(project_id, module_id, artifact["type"])
    previous = None
    for h in reversed(history):
        if h["id"] != artifact["id"]:
            previous = h
            break

    if previous and artifact.get("content") and previous.get("content"):
        st.markdown(f"**Diff vs previous version (v{previous['version']}, {previous['status']}):**")
        differ = difflib.HtmlDiff(wrapcolumn=80)
        html = differ.make_table(
            previous["content"].splitlines(),
            artifact["content"].splitlines(),
            fromdesc=f"v{previous['version']}",
            todesc=f"v{artifact['version']} (about to be baselined)",
            context=True, numlines=3
        )
        # HtmlDiff produces a bare table - wrap with minimal styling so it's readable
        styled = f"""
        <style>
          table.diff {{font-family: monospace; font-size: 12px; width: 100%; border-collapse: collapse;}}
          td.diff_header {{background: #f2f2f2;}}
          .diff_add {{background-color: #d4f7d4;}}
          .diff_chg {{background-color: #fff3b0;}}
          .diff_sub {{background-color: #ffd6d6;}}
        </style>
        {html}
        """
        st.components.v1.html(styled, height=400, scrolling=True)
    elif not previous:
        st.info("No previous version to compare against — this would be the first baseline.")
    else:
        st.warning("⚠️ Diff unavailable for this artifact type (no text content, e.g. DD/CT spreadsheets) — review the file directly before confirming.")

    # ── CONFIRMATION ─────────────────────────────────────────────────────────
    description = st.text_area(
        "Change description (required — feeds the Revision History and SCMP SCI Register)",
        placeholder="ex: Approved for SOI #1 — corrected memory map, aligned with ARCH",
        key=f"desc_{artifact['id']}"
    )
    baselined_by = st.text_input("Baselined by", key=f"by_{artifact['id']}")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✅ Confirm baseline", type="primary",
                     disabled=not description.strip(), key=f"confirm_{artifact['id']}"):
            new_id = baseline_artifact(artifact["id"], description, baselined_by or "unknown")
            st.session_state[show_key] = False
            st.success(f"🔒 Baselined — new artifact id {new_id}")
            st.rerun()
    with col2:
        if st.button("Cancel", key=f"cancel_{artifact['id']}"):
            st.session_state[show_key] = False
            st.rerun()


def render_text_artifact(artifact, module_id):
    content = artifact.get("content", "")
    if module_id == "M3":
        st.code(content[:5000], language="c")
        if len(content) > 5000:
            st.caption(f"... showing first 5000 of {len(content):,} chars")
    else:
        st.text_area("Full content", value=content, height=350,
                     key=f"content_{artifact['type']}_{artifact['id']}", disabled=True)
    st.download_button(
        label=f"⬇️ Download {artifact['type']}",
        data=content, file_name=f"{artifact['type']}_{active['name']}.txt",
        mime="text/plain", key=f"dl_{artifact['type']}_{artifact['id']}"
    )


def render_xlsx_artifact(artifact):
    path = artifact.get("file_path", "")
    if not path or not os.path.exists(path):
        st.warning(f"⚠️ File not found on disk: {path or '(no path saved)'}")
        return
    try:
        import pandas as pd
        xls = pd.ExcelFile(path)
        tabs = st.tabs(xls.sheet_names)
        for tab, sheet in zip(tabs, xls.sheet_names):
            with tab:
                df = xls.parse(sheet)
                st.dataframe(df, use_container_width=True, height=300)
    except Exception as e:
        st.error(f"⚠️ Could not preview spreadsheet: {e}")
    with open(path, "rb") as f:
        st.download_button(
            label=f"⬇️ Download {artifact['type']}.xlsx",
            data=f.read(), file_name=os.path.basename(path),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{artifact['type']}_{artifact['id']}"
        )


# ── ARTIFACT VIEWER ───────────────────────────────────────────────────────────
for module_id in ["M1", "M2", "M3", "M4", "M5", "M6"]:
    if module_id not in by_module:
        continue

    module_desc, expected_types = MODULE_INFO[module_id]
    module_files = by_module[module_id]
    prev_review = existing_reviews.get(module_id)

    status_icon = ("✅" if prev_review and prev_review["status"] == "approved"
                   else "⚠️" if prev_review and prev_review["status"] == "needs_revision"
                   else "❌" if prev_review and prev_review["status"] == "rejected"
                   else "⬜")

    present_types = [t for t in expected_types if t in module_files]
    types_label = " + ".join(present_types) if present_types else "no output yet"

    with st.expander(
        f"{status_icon} {module_id} — {types_label} {module_desc}",
        expanded=(module_id == "M1")
    ):
        tab_labels = [f"📄 {t}" for t in present_types] + ["✏️ Review"]
        tabs = st.tabs(tab_labels)

        for tab, artifact_type in zip(tabs, present_types):
            with tab:
                artifact = module_files[artifact_type]
                st.caption(
                    f"Generated: {artifact.get('created_at', '')[:16]} | "
                    f"Version: {artifact.get('version', 1)}"
                )
                if artifact_type in ("DD", "CT"):
                    render_xlsx_artifact(artifact)
                else:
                    render_text_artifact(artifact, module_id)
                render_baseline_section(artifact, active["id"], module_id)

        # ── REVIEW TAB (last tab) ───────────────────────────────────────────
        with tabs[-1]:
            st.markdown("**Review decision:**")

            status_options = ["approved", "needs_revision", "rejected"]
            status_labels = {
                "approved": "✅ Approved",
                "needs_revision": "⚠️ Needs revision",
                "rejected": "❌ Rejected"
            }
            current_status = prev_review["status"] if prev_review else "needs_revision"

            col1, col2 = st.columns([1, 2])
            with col1:
                status = st.radio(
                    "Status", status_options,
                    format_func=lambda x: status_labels[x],
                    index=status_options.index(current_status),
                    key=f"status_{module_id}"
                )
            with col2:
                notes = st.text_area(
                    "Review notes",
                    value=prev_review["notes"] if prev_review else "",
                    placeholder="ex: HLR-006 timing incorrect, split into 2...\n"
                                "ex: LLR-CLK-002-01 missing timeout handling...",
                    height=120, key=f"notes_{module_id}"
                )
                reviewer = st.text_input(
                    "Reviewer name",
                    value=prev_review.get("reviewer", "") if prev_review else "",
                    key=f"reviewer_{module_id}"
                )

            if st.button(f"💾 Save review {module_id}", key=f"save_{module_id}", type="primary"):
                save_review(active["id"], module_id, "+".join(present_types), status, notes, reviewer)
                st.success(f"✅ Review saved — {status_labels[status]}")
                if status in ["needs_revision", "rejected"]:
                    st.info("👉 Go to **5 TC Excel** to document your technical remarks for re-generation.")
                st.rerun()

st.divider()

# ── GLOBAL ACTIONS ────────────────────────────────────────────────────────────
reviews = get_reviews(active["id"])
approved_count = sum(1 for r in reviews if r["status"] == "approved")

if approved_count == len(by_module) == 6:
    st.success("🎉 All 6 modules approved! Project complete.")
elif len(reviews) > 0:
    needs_fix = sum(1 for r in reviews if r["status"] in ["needs_revision", "rejected"])
    if needs_fix > 0:
        st.warning(
            f"⚠️ {needs_fix} artifact(s) need revision. "
            "Go to **5 TC Excel** to add technical remarks, "
            "then re-run the module on **2 Pipeline**."
        )