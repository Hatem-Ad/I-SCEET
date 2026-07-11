"""
================================================================================
 I-SCEET — Accueil
 File: ui/app.py
================================================================================
"""

import streamlit as st
import sys, os
import textwrap

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Backend.db import get_all_projects, get_artifacts, get_reviews, get_tc_remarks
from theme import inject_theme, module_rail, nav_card

st.set_page_config(page_title="I-SCEET", page_icon="/", layout="wide")
inject_theme()

# ── DONNÉES PROJET ACTIF ──────────────────────────────────────────────────────
active = st.session_state.get("active_project")
all_projects = get_all_projects()

modules_done = set()
if active:
    artifacts = get_artifacts(active["id"])
    reviews = get_reviews(active["id"])
    tc = get_tc_remarks(active["id"])
    modules_done = {a["module"] for a in artifacts if a["module"] in
                    ["M1", "M2", "M3", "M4", "M5", "M6"]}

# ── HERO ────────────────────────────────────────────────────────────────────
dal_html = ""
if active:
    dal_html = textwrap.dedent(f"""
    <div class="isc-dal-badge">
        <div class="lbl">DAL</div>
        <div class="val">{active['dal_level']}</div>
    </div>""")

st.markdown(textwrap.dedent(f"""
<div class="isc-hero">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1.5rem;flex-wrap:wrap">
    <div>
      <div class="isc-eyebrow">I-SCEET</div>
      <div class="isc-hero-title">Intelligent Safety-Critical Engineering Environment Toolchain</div>
      <div class="isc-hero-tag">Chaîne de génération assistée par IA, entièrement traçable, conforme DO-178C
      DAL A — des exigences au code jusqu'à la vérification, pour systèmes embarqués
      de classe régulation moteur.</div>
    </div>
    {dal_html}
  </div>
</div>
"""), unsafe_allow_html=True)

module_rail(
    modules_done,
    label=f"PIPELINE M1 \u2192 M6 — {active['name']}" if active else "PIPELINE M1 \u2192 M6 — aucun projet actif"
)

st.write("")

# ── APERÇU PROJET ACTIF ────────────────────────────────────────────────────
if active:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pipeline", f"{len(modules_done)}/6 modules")
    c2.metric("Approuvés", sum(1 for r in reviews if r["status"] == "approved"))
    c3.metric("Remarques ouvertes", sum(1 for t in tc if t["status"] == "open"))
    c4.metric("Statut", active.get("status", "in_progress"))

    bcol1, bcol2 = st.columns(2)
    with bcol1:
        st.page_link("pages/2_pipeline.py", label="Poursuivre le pipeline")
    with bcol2:
        st.page_link("pages/3_revue.py", label="Réviser les artefacts")
else:
    st.info(
        f"Aucun projet actif. "
        f"{'Sélectionnez-en un dans **Historique**, ou ' if all_projects else ''}"
        f"démarrez un **nouveau projet** ci-dessous."
    )

st.divider()

# ── NAVIGATION ──────────────────────────────────────────────────────────────
st.markdown('<div class="isc-eyebrow">Naviguer</div>', unsafe_allow_html=True)

NAV = [
    ("01", "pages/1_upload.py", "Nouveau projet / Upload",
     "Créer un projet et téléverser PDS, architecture, documentation matérielle, et les 9 documents de planning/standards."),
    ("02", "pages/2_pipeline.py", "Pipeline M1 \u2192 M6",
     "Se connecter à Colab et exécuter le pipeline IA : HLR, LLR, code, tests, traçabilité."),
    ("03", "pages/3_revue.py", "Revue des artefacts",
     "Inspecter chaque artefact généré (SRD, SDDD, DD, CT, /src, SUTC, SVTC, TM) et approuver ou signaler."),
    ("04", "pages/4_chat_tc.py", "Chat consultatif",
     "Interroger les artefacts générés — strictement consultatif, ne modifie aucune sortie."),
    ("05", "pages/5_tc_excel.py", "Remarques techniques",
     "Consigner une remarque, l'envoyer au module IA responsable, et confirmer la correction."),
    ("06", "pages/6_historique.py", "Historique du projet",
     "Parcourir, réactiver ou supprimer d'anciens projets et consulter leur historique complet."),
]

for row_start in range(0, len(NAV), 3):
    cols = st.columns(3)
    for col, (num, page, title, desc) in zip(cols, NAV[row_start:row_start + 3]):
        with col:
            nav_card(num, title, desc)
            st.page_link(page, label="Ouvrir")
            st.write("")

st.divider()
st.caption(
    "I-SCEET — projet de validation : "
    "bootloader et pilotes STM32F303VCT6 pour un calculateur de régulation moteur de classe FADEC."
)
