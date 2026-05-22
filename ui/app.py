"""
================================================================================
 I-SCEET — Streamlit Main Entry Point
 File: ui/app.py
 Run: streamlit run app.py (from ui/ folder)
================================================================================
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Backend.db import get_all_projects, get_artifacts

st.set_page_config(
    page_title="I-SCEET",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✈️ I-SCEET")
    st.caption("Intelligent Safety-Critical Engineering Environment Toolchain")
    st.divider()

    projects = get_all_projects()
    if projects:
        project_names = ["— Sélectionner —"] + [p["name"] for p in projects]
        selected = st.selectbox("Projet actif", project_names)

        if selected != "— Sélectionner —":
            project = next(p for p in projects if p["name"] == selected)
            st.session_state["active_project"] = project

            st.divider()
            st.markdown(f"**Projet :** {project['name']}")
            st.markdown(f"**DAL :** {project['dal_level']}")

            status_color = {
                "in_progress": "🟡",
                "complete":    "🟢",
                "error":       "🔴",
            }
            st.markdown(f"**Statut :** {status_color.get(project['status'], '⚪')} {project['status']}")

            artifacts = get_artifacts(project["id"])
            modules_done = [a["module"] for a in artifacts]
            st.divider()
            st.markdown("**Pipeline :**")
            for m in ["M1", "M2", "M3", "M4", "M5", "M6"]:
                icon = "✅" if m in modules_done else "⬜"
                st.markdown(f"{icon} {m}")
    else:
        st.info("Aucun projet. Créez-en un via **1 Upload**.")
        if "active_project" in st.session_state:
            del st.session_state["active_project"]

    st.divider()
    st.caption("DO-178C DAL A — v1.0")

# ── MAIN PAGE ─────────────────────────────────────────────────────────────────
st.title("✈️ I-SCEET")
st.subheader("Intelligent Safety-Critical Engineering Environment Toolchain")
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🎯 Objectif")
    st.markdown("""
    Automatiser la chaîne **DO-178C** de bout en bout
    avec des modèles IA locaux et spécialisés.
    """)

with col2:
    st.markdown("### ⚙️ Pipeline")
    st.markdown("""
    **M1** HLR → **M2** LLR → **M3** Code
    → **M4** LLT → **M5** HLT → **M6** Traçabilité
    """)

with col3:
    st.markdown("### 🔒 Sécurité")
    st.markdown("""
    100% **local** — aucune donnée ne quitte
    votre infrastructure. Conforme aéro-défense.
    """)

st.divider()

# Stats
projects = get_all_projects()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Projets", len(projects))
c2.metric("DAL A", sum(1 for p in projects if p["dal_level"] == "A"))
c3.metric("Terminés", sum(1 for p in projects if p["status"] == "complete"))
c4.metric("En cours", sum(1 for p in projects if p["status"] == "in_progress"))

st.divider()
st.markdown("👈 **Utilisez le menu latéral pour naviguer entre les pages.**")
