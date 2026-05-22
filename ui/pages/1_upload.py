"""
================================================================================
 I-SCEET — Page 1 : Upload documents + Nouveau projet
 File: ui/pages/1_upload.py
================================================================================
"""

import streamlit as st
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from Backend.db import create_project, get_all_projects, save_artifact

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="Upload — I-SCEET", page_icon="📤", layout="wide")
st.title("📤 Nouveau projet — Upload documents")
st.divider()

# ── STEP 1 : PROJECT ──────────────────────────────────────────────────────────
st.markdown("### Étape 1 — Créer le projet")
col1, col2 = st.columns([2, 1])
with col1:
    project_name = st.text_input("Nom du projet", placeholder="ex: STM32F303_Bootloader_v1")
with col2:
    dal_level = st.selectbox("Niveau DAL", ["A", "B", "C", "D"])

if st.button("➕ Créer le projet", type="primary", disabled=not project_name):
    existing = [p["name"] for p in get_all_projects()]
    if project_name in existing:
        st.error(f"Un projet nommé **{project_name}** existe déjà.")
    else:
        pid = create_project(project_name, dal_level)
        st.session_state["active_project"] = {"id": pid, "name": project_name, "dal_level": dal_level}
        st.success(f"✅ Projet **{project_name}** créé (ID: {pid})")

st.divider()

# ── STEP 2 : PLANNING & STANDARDS ────────────────────────────────────────────
st.markdown("### Étape 2 — Documents DO-178C (10 documents)")
st.caption("Plans et standards — injectés dans chaque module")

planning_docs = {
    "PSAC-001": "Plan for Software Aspects of Certification",
    "SDP-001":  "Software Development Plan",
    "SVP-001":  "Software Verification Plan",
    "SCMP-001": "Software Configuration Management Plan",
    "SQAP-001": "Software Quality Assurance Plan",
    "SRS-001":  "Software Requirements Standards",
    "SDS-001":  "Software Design Standards",
    "SCS-001":  "Software Code Standards",
}

uploaded_planning = {}
cols = st.columns(2)
for i, (doc_id, doc_name) in enumerate(planning_docs.items()):
    with cols[i % 2]:
        f = st.file_uploader(f"{doc_id} — {doc_name}", type=["docx", "pdf", "txt"],
                             key=f"plan_{doc_id}")
        if f:
            uploaded_planning[doc_id] = f

st.divider()

# ── STEP 3 : M1 INPUTS ────────────────────────────────────────────────────────
st.markdown("### Étape 3 — Inputs M1 (3 documents)")
st.caption("Documents source pour la génération des HLR")

col1, col2, col3 = st.columns(3)
with col1:
    pds_file = st.file_uploader("📄 PDS — Product Design Specification",
                                type=["docx", "pdf", "txt"], key="pds")
with col2:
    arch_file = st.file_uploader("🏗️ Architecture Système",
                                 type=["docx", "pdf", "txt"], key="arch")
with col3:
    hw_file = st.file_uploader("🔧 Hardware Documentation",
                               type=["docx", "pdf", "txt"], key="hw")

st.divider()

# ── SAVE ──────────────────────────────────────────────────────────────────────
all_uploaded = len(uploaded_planning) == 8 and pds_file and arch_file and hw_file
active = st.session_state.get("active_project")

if not active:
    st.warning("⚠️ Créez ou sélectionnez un projet avant de sauvegarder.")

if st.button("💾 Sauvegarder tous les documents", type="primary",
             disabled=not (active and all_uploaded)):
    pid = active["id"]
    saved = 0

    def save_file(file, doc_type, module):
        global saved
        path = os.path.join(UPLOAD_DIR, f"{pid}_{doc_type}_{file.name}")
        with open(path, "wb") as f:
            f.write(file.read())
        content = f"[FILE: {file.name}]"
        save_artifact(pid, module, doc_type, content, path)
        saved += 1

    for doc_id, f in uploaded_planning.items():
        save_file(f, doc_id, "PLANNING")

    save_file(pds_file,  "PDS",  "M1_INPUT")
    save_file(arch_file, "ARCH", "M1_INPUT")
    save_file(hw_file,   "HW",   "M1_INPUT")

    st.success(f"✅ {saved} documents sauvegardés dans la base de données !")
    st.info("👉 Allez sur **2 Pipeline** pour lancer la génération M1→M6")
else:
    missing = 11 - len(uploaded_planning) - (1 if pds_file else 0) - \
              (1 if arch_file else 0) - (1 if hw_file else 0)
    if missing > 0:
        st.info(f"📎 {missing} document(s) manquant(s) avant de pouvoir sauvegarder.")
