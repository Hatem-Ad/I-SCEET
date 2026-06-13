"""
================================================================================
 I-SCEET — Page 3 : Revue globale
 File: ui/pages/3_revue.py
================================================================================
"""

import streamlit as st
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from Backend.db import get_artifacts, save_review, get_reviews

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
module_artifacts = {a["module"]: a for a in artifacts
                    if a["module"] in ["M1","M2","M3","M4","M5","M6"]}

if not module_artifacts:
    st.info("⬜ No artifacts yet. Run the pipeline on **2 Pipeline** first.")
    st.stop()

existing_reviews = {r["module"]: r for r in get_reviews(active["id"])}

MODULE_INFO = {
    "M1": ("SRD-001",      "📋 High Level Requirements"),
    "M2": ("SDDD-001",     "📐 Low Level Requirements + Architecture"),
    "M3": ("/src",         "💻 Source Code C"),
    "M4": ("SVCP-LLT-001", "🧪 Low Level Tests"),
    "M5": ("SVCP-HLT-001", "🧪 High Level Tests"),
    "M6": ("STD-001",      "🗺️ Traceability Matrix"),
}

# ── SUMMARY BAR ───────────────────────────────────────────────────────────────
reviews = get_reviews(active["id"])
c1, c2, c3, c4 = st.columns(4)
c1.metric("Modules generated", f"{len(module_artifacts)}/6")
c2.metric("✅ Approved",  sum(1 for r in reviews if r["status"] == "approved"))
c3.metric("⚠️ Revision",  sum(1 for r in reviews if r["status"] == "needs_revision"))
c4.metric("❌ Rejected",  sum(1 for r in reviews if r["status"] == "rejected"))

st.divider()

# ── ARTIFACT VIEWER ───────────────────────────────────────────────────────────
for module_id in ["M1","M2","M3","M4","M5","M6"]:
    if module_id not in module_artifacts:
        continue

    artifact     = module_artifacts[module_id]
    doc_name, doc_desc = MODULE_INFO.get(module_id, (module_id, ""))
    prev_review  = existing_reviews.get(module_id)
    content      = artifact.get("content", "")

    status_icon = "✅" if prev_review and prev_review["status"] == "approved" \
                  else "⚠️" if prev_review and prev_review["status"] == "needs_revision" \
                  else "❌" if prev_review and prev_review["status"] == "rejected" \
                  else "⬜"

    with st.expander(
        f"{status_icon} {module_id} — {doc_name} {doc_desc} "
        f"({len(content):,} chars)",
        expanded=(module_id == "M1")  # M1 open by default
    ):
        tab1, tab2 = st.tabs(["📄 Content", "✏️ Review"])

        # ── TAB 1 : CONTENT VIEWER ────────────────────────────────────────────
        with tab1:
            st.caption(
                f"Generated: {artifact.get('created_at', '')[:16]} | "
                f"Version: {artifact.get('version', 1)}"
            )

            if module_id == "M3":
                # Code viewer with syntax highlighting
                st.code(content[:5000], language="c")
                if len(content) > 5000:
                    st.caption(f"... showing first 5000 of {len(content):,} chars")
            else:
                # Text viewer with scroll
                st.text_area(
                    "Full content",
                    value=content,
                    height=400,
                    key=f"content_{module_id}",
                    disabled=True
                )

            # Download button
            st.download_button(
                label=f"⬇️ Download {doc_name}",
                data=content,
                file_name=f"{doc_name}_{active['name']}.txt",
                mime="text/plain",
                key=f"dl_{module_id}"
            )

        # ── TAB 2 : REVIEW ────────────────────────────────────────────────────
        with tab2:
            st.markdown("**Review decision:**")

            status_options = ["approved", "needs_revision", "rejected"]
            status_labels  = {
                "approved":       "✅ Approved",
                "needs_revision": "⚠️ Needs revision",
                "rejected":       "❌ Rejected"
            }
            current_status = prev_review["status"] \
                if prev_review else "needs_revision"

            col1, col2 = st.columns([1, 2])
            with col1:
                status = st.radio(
                    "Status",
                    status_options,
                    format_func=lambda x: status_labels[x],
                    index=status_options.index(current_status),
                    key=f"status_{module_id}"
                )

            with col2:
                notes = st.text_area(
                    "Review notes",
                    value=prev_review["notes"] if prev_review else "",
                    placeholder="ex: HLR-006 timing incorrect, split into 2...\n"
                                "ex: LLR-012 missing timeout handling...",
                    height=120,
                    key=f"notes_{module_id}"
                )
                reviewer = st.text_input(
                    "Reviewer name",
                    value=prev_review.get("reviewer", "") if prev_review else "",
                    key=f"reviewer_{module_id}"
                )

            if st.button(
                f"💾 Save review {module_id}",
                key=f"save_{module_id}",
                type="primary"
            ):
                save_review(
                    active["id"], module_id,
                    doc_name, status, notes, reviewer
                )
                st.success(
                    f"✅ Review saved — {status_labels[status]}"
                )
                if status in ["needs_revision", "rejected"]:
                    st.info(
                        "👉 Go to **5 TC Excel** to document your "
                        "technical remarks for re-generation."
                    )
                st.rerun()

st.divider()

# ── GLOBAL ACTIONS ────────────────────────────────────────────────────────────
reviews = get_reviews(active["id"])
approved_count = sum(1 for r in reviews if r["status"] == "approved")

if approved_count == len(module_artifacts) and len(module_artifacts) == 6:
    st.success("🎉 All 6 artifacts approved! Project complete.")
elif len(reviews) > 0:
    needs_fix = sum(1 for r in reviews
                    if r["status"] in ["needs_revision", "rejected"])
    if needs_fix > 0:
        st.warning(
            f"⚠️ {needs_fix} artifact(s) need revision. "
            "Go to **5 TC Excel** to add technical remarks, "
            "then re-run the module on **2 Pipeline**."
        )
