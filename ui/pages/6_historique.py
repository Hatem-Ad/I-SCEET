"""
================================================================================
 I-SCEET — Page 6 : Historique des projets
 File: ui/pages/6_historique.py
 Copyright (c) 2026 Hatem Adouani — MIT License
================================================================================
"""

import streamlit as st
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Backend.db import (
    get_all_projects,
    get_artifacts,
    get_reviews,
    get_tc_remarks,
    delete_project,
    get_all_baselines,
    set_active_project_id,
)
from theme import inject_theme, page_header, module_rail, badge, render_sci_table

st.set_page_config(page_title="Historique — I-SCEET", layout="wide")
inject_theme()
page_header("WORKSPACE 06 • CONFIGURATION", "Historique des projets & enregistrements SCI", "Inspect project history, review completion, baseline records and lifecycle configuration evidence.")

creation_notice = st.session_state.pop("history_notice", None)
if creation_notice:
    st.success(creation_notice)

projects = get_all_projects()

if not projects:
    st.info("Aucun projet. Créez-en un via **1 Upload**.")
    st.stop()

status_icon = {"in_progress": "🟡", "complete": "🟢", "error": "🔴"}
MODULES = ["M1","M2","M3","M4","M5","M6"]

for p in projects:
    artifacts = get_artifacts(p["id"])
    reviews   = get_reviews(p["id"])
    tc        = get_tc_remarks(p["id"])
    done_modules = {a["module"] for a in artifacts if a["module"] in MODULES}

    generated_modules = done_modules
    effective_status = "complete" if len(generated_modules) == 6 else p.get("status", "in_progress")
    icon = status_icon.get(effective_status, "⚪")
    with st.expander(f"{icon}  {p['name']} — DAL {p['dal_level']} — {p['created_at'][:10]}"):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Modules générés", f"{len(done_modules)}/6")
        col2.metric("Revues",          len(reviews))
        col3.metric("Remarques TC",    len(tc))
        col4.metric("Statut",          p["status"])

        module_rail(done_modules, label="", light=True)

        if artifacts:
            st.markdown("**Artefacts :**")
            for a in artifacts:
                if a["module"] in MODULES:
                    st.caption(f"• {a['module']} → {a['type']} — v{a['version']} — {a['created_at'][:16]}")

        if reviews:
            st.markdown("**Revues :**")
            approved = sum(1 for r in reviews if r["status"] == "approved")
            st.markdown(badge(f"{approved} approuvés / {len(reviews)} total", "success"), unsafe_allow_html=True)

        # ── SCI REGISTER (feeds SCMP §8) ─────────────────────────────────────
        baselines = get_all_baselines(p["id"])
        if baselines:
            st.markdown('<div class="isc-eyebrow">SCI Register — baselines (alimente SCMP §8)</div>', unsafe_allow_html=True)
            sci_rows = [{
                "Document ID": f"{b['type']}-{b['baseline_number']}" if b['type'] not in
                    ("PSAC", "SDP", "SVP", "SCMP", "SQAP") else b['type'],
                "Version": b["version"],
                "Baselined": (b.get("baselined_at") or "")[:16],
                "By": b.get("baselined_by") or "—",
                "Description": b.get("change_description") or "—",
            } for b in baselines]
            render_sci_table(sci_rows, width="stretch", columns=["Document ID","Version","Baselined","By","Description",],)
            import pandas as pd
            csv = pd.DataFrame(sci_rows).to_csv(index=False).encode("utf-8")
            st.download_button(
                "Exporter le SCI Register (CSV — à coller dans SCMP §8)",
                data=csv, file_name=f"SCI_Register_{p['name']}.csv",
                mime="text/csv", key=f"sci_{p['id']}"
            )

        st.divider()
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Activer ce projet", key=f"activate_{p['id']}"):
                # Keep the selected project available on every workspace.
                st.session_state["active_project"] = p
                set_active_project_id(p["id"])
                st.switch_page("pages/2_pipeline.py")

        with col2:
            if st.button("Voir TC", key=f"tc_{p['id']}"):
                # "Voir TC" also activates the project represented by this row.
                # This avoids requiring a separate activation click and guarantees
                # that Workspace 05 receives the correct project context.
                st.session_state["active_project"] = p
                set_active_project_id(p["id"])
                st.switch_page("pages/5_tc_excel.py")

        with col3:
            if st.button("Supprimer", key=f"delete_{p['id']}", type="secondary"):
                if st.session_state.get(f"confirm_delete_{p['id']}"):
                    delete_project(p["id"])
                    if st.session_state.get("active_project", {}).get("id") == p["id"]:
                        st.session_state.pop("active_project", None)
                    st.success("Projet supprimé.")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_{p['id']}"] = True
                    st.warning("Cliquez à nouveau pour confirmer la suppression.")