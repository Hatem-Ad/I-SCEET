"""
================================================================================
 I-SCEET — Page 6 : Historique des projets
 File: ui/pages/6_historique.py
================================================================================
"""

import streamlit as st
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from Backend.db import (get_all_projects, get_artifacts,
                         get_reviews, get_tc_remarks, delete_project)

st.set_page_config(page_title="Historique — I-SCEET", page_icon="📁", layout="wide")
st.title("📁 Historique des projets")
st.divider()

projects = get_all_projects()

if not projects:
    st.info("Aucun projet. Créez-en un via **1 Upload**.")
    st.stop()

status_icons = {"in_progress": "🟡", "complete": "🟢", "error": "🔴"}
MODULES = ["M1","M2","M3","M4","M5","M6"]

for p in projects:
    artifacts = get_artifacts(p["id"])
    reviews   = get_reviews(p["id"])
    tc        = get_tc_remarks(p["id"])
    done_modules = [a["module"] for a in artifacts if a["module"] in MODULES]

    icon = status_icons.get(p["status"], "⚪")
    with st.expander(f"{icon} {p['name']} — DAL {p['dal_level']} — {p['created_at'][:10]}"):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Modules générés", f"{len(done_modules)}/6")
        col2.metric("Revues",          len(reviews))
        col3.metric("TC Remarks",      len(tc))
        col4.metric("Statut",          p["status"])

        st.markdown("**Pipeline :**")
        pipeline_str = " → ".join([
            f"{'✅' if m in done_modules else '⬜'} {m}"
            for m in MODULES
        ])
        st.markdown(pipeline_str)

        if artifacts:
            st.markdown("**Artefacts :**")
            for a in artifacts:
                if a["module"] in MODULES:
                    st.caption(f"• {a['module']} → {a['type']} — v{a['version']} — {a['created_at'][:16]}")

        if reviews:
            st.markdown("**Revues :**")
            approved = sum(1 for r in reviews if r["status"] == "approved")
            st.caption(f"✅ {approved} approuvés / {len(reviews)} total")

        st.divider()
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📂 Activer ce projet", key=f"activate_{p['id']}"):
                st.session_state["active_project"] = p
                st.success(f"✅ Projet **{p['name']}** activé !")
                st.rerun()

        with col2:
            if st.button("📊 Voir TC", key=f"tc_{p['id']}"):
                st.session_state["active_project"] = p
                st.switch_page("pages/5_tc_excel.py")

        with col3:
            if st.button("🗑️ Supprimer", key=f"delete_{p['id']}", type="secondary"):
                if st.session_state.get(f"confirm_delete_{p['id']}"):
                    delete_project(p["id"])
                    if st.session_state.get("active_project", {}).get("id") == p["id"]:
                        del st.session_state["active_project"]
                    st.success("Projet supprimé.")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_{p['id']}"] = True
                    st.warning("Cliquez à nouveau pour confirmer la suppression.")
