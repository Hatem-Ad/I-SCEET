"""
================================================================================
 I-SCEET — Page 4 : Chat consultatif / TC
 File: ui/pages/4_chat_tc.py
================================================================================
 v2: was calling nothing — the answer was always the literal string
 "[Appel API Colab à implémenter]", a TODO that was never done. The
 Colab notebook (01_colab_server.ipynb, Cell 11) already has a working
 POST /chat endpoint (M6/Phi-4, independent, consultative) — this page
 now actually calls it via PCPipeline.chat().
================================================================================
"""

import streamlit as st
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from Backend.db import get_artifacts, save_chat, get_chat_history
from orchestrator.pc_pipeline import PCPipeline

st.set_page_config(page_title="Chat — I-SCEET", page_icon="💬", layout="wide")
st.title("💬 Chat consultatif")
st.caption("Posez des questions sur les artefacts générés. Consultatif uniquement — ne modifie pas les outputs. Modèle : M6 (Phi-4), indépendant des générateurs.")
st.divider()

active = st.session_state.get("active_project")
if not active:
    st.warning("⚠️ Aucun projet actif. Retournez sur **1 Upload**.")
    st.stop()

artifacts = get_artifacts(active["id"])

# One artifact per module for chat context - prefer the one with the most
# text content (DD/CT have empty content, only SDDD/SRD/etc. carry text;
# picking by length avoids accidentally grabbing an empty-content row).
module_artifacts = {}
for a in artifacts:
    if a["module"] not in ["M1", "M2", "M3", "M4", "M5", "M6"]:
        continue
    current = module_artifacts.get(a["module"])
    if current is None or len(a.get("content") or "") > len(current.get("content") or ""):
        module_artifacts[a["module"]] = a

if not module_artifacts:
    st.info("⬜ Aucun artefact généré. Lancez d'abord le pipeline.")
    st.stop()

colab_url = st.session_state.get("colab_url", "")

col1, col2 = st.columns([1, 3])
with col1:
    target_options = list(module_artifacts.keys()) + ["ALL"]
    target = st.selectbox("Interroger", target_options,
                          format_func=lambda x: f"{x} — Tous les modules" if x == "ALL" else x)

with col2:
    st.markdown(f"**Cible :** {target}")
    if target == "ALL":
        st.caption("Le modèle lira tous les artefacts générés pour répondre.")
    else:
        artifact = module_artifacts.get(target)
        st.caption(f"Artefact : {artifact['type']} — {len(artifact.get('content','')):,} caractères")

st.divider()

history = get_chat_history(active["id"])
if history:
    st.markdown("### Historique")
    for h in history[-10:]:
        with st.chat_message("user"):
            st.markdown(f"**[{h['target']}]** {h['question']}")
        with st.chat_message("assistant"):
            st.markdown(h["answer"])

question = st.chat_input("Posez votre question sur les artefacts...")

if question:
    with st.chat_message("user"):
        st.markdown(f"**[{target}]** {question}")

    with st.chat_message("assistant"):
        if not colab_url:
            answer = (
                f"**[Mode simulation — Colab non connecté]**\n\n"
                f"Question reçue pour **{target}** : *{question}*\n\n"
                f"Connecte Colab sur **2 Pipeline** pour une vraie réponse."
            )
            st.markdown(answer)
        else:
            with st.spinner("🧠 M6 (Phi-4) analyse les artefacts... (peut prendre 1-2 min si le modèle doit charger)"):
                pipeline = PCPipeline(colab_url, active["id"])
                chat_artifacts = {m: a.get("content", "") for m, a in module_artifacts.items()}
                result = pipeline.chat(target, question, chat_artifacts)

            if result.get("status") == "success":
                answer = result.get("answer", "(empty response)")
            else:
                answer = f"⚠️ {result.get('answer', 'Unknown error')}"
            st.markdown(answer)

        save_chat(active["id"], target, question, answer)

st.divider()
st.caption("⚠️ Le chat est consultatif. Pour corriger un artefact → utilisez **5 TC Excel** puis relancez le module.")