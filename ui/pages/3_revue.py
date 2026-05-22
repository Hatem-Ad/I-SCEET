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
    st.warning("⚠️ Aucun projet actif. Retournez sur **1 Upload**.")
    st.stop()

st.markdown(f"**Projet :** {active['name']} — DAL {active['dal_level']}")
st.divider()

artifacts = get_artifacts(active["id"])
module_artifacts = {a["module"]: a for a in artifacts
                    if a["module"] in ["M1","M2","M3","M4","M5","M6"]}

if not module_artifacts:
    st.info("⬜ Aucun artefact généré. Lancez d'abord le pipeline sur **2 Pipeline**.")
    st.stop()

existing_reviews = {r["module"]: r for r in get_reviews(active["id"])}

MODULE_INFO = {
    "M1": ("SRD-001",      "HLRs générés"),
    "M2": ("SDDD-001",     "LLRs + Architecture"),
    "M3": ("/src",         "Code source C"),
    "M4": ("SVCP-LLT-001", "Tests bas niveau"),
    "M5": ("SVCP-HLT-001", "Tests haut niveau"),
    "M6": ("STD-001",      "Matrice de traçabilité"),
}

for module_id, artifact in sorted(module_artifacts.items()):
    doc_name, doc_desc = MODULE_INFO.get(module_id, (module_id, ""))
    prev_review = existing_reviews.get(module_id)

    with st.expander(f"{'✅' if prev_review and prev_review['status'] == 'approved' else '⬜'} "
                     f"{module_id} — {doc_name} ({doc_desc})", expanded=False):

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("**Contenu généré :**")
            content = artifact.get("content", "")
            st.text_area("Output", value=content[:3000] + ("..." if len(content) > 3000 else ""),
                         height=200, key=f"content_{module_id}", disabled=True)

        with col2:
            st.markdown("**Décision de revue :**")
            status_options = ["approved", "needs_revision", "rejected"]
            status_labels  = {"approved": "✅ Approuvé", "needs_revision": "⚠️ À corriger", "rejected": "❌ Rejeté"}
            current_status = prev_review["status"] if prev_review else "needs_revision"

            status = st.radio(
                "Statut",
                status_options,
                format_func=lambda x: status_labels[x],
                index=status_options.index(current_status),
                key=f"status_{module_id}"
            )

            notes = st.text_area(
                "Notes de revue",
                value=prev_review["notes"] if prev_review else "",
                placeholder="Ex: HLR-006 timing incorrect, diviser en 2...",
                height=120,
                key=f"notes_{module_id}"
            )

            reviewer = st.text_input(
                "Réviseur",
                value=prev_review.get("reviewer", "") if prev_review else "",
                key=f"reviewer_{module_id}"
            )

            if st.button(f"💾 Sauvegarder revue {module_id}", key=f"save_{module_id}"):
                save_review(
                    active["id"], module_id,
                    doc_name, status, notes, reviewer
                )
                st.success(f"✅ Revue {module_id} sauvegardée — {status_labels[status]}")
                st.rerun()

st.divider()

# Summary
reviews = get_reviews(active["id"])
if reviews:
    st.markdown("### Résumé des revues")
    approved = sum(1 for r in reviews if r["status"] == "approved")
    revision = sum(1 for r in reviews if r["status"] == "needs_revision")
    rejected = sum(1 for r in reviews if r["status"] == "rejected")

    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Approuvés", approved)
    c2.metric("⚠️ À corriger", revision)
    c3.metric("❌ Rejetés", rejected)

    if rejected > 0 or revision > 0:
        st.info("👉 Allez sur **5 TC Excel** pour documenter vos remarques techniques.")
    elif approved == len(module_artifacts):
        st.success("🎉 Tous les artefacts sont approuvés !")
