"""
================================================================================
 I-SCEET — Page 2 : Pipeline M1→M6
 File: ui/pages/2_pipeline.py
================================================================================
"""

import streamlit as st
import sys, os, time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from Backend.db import get_artifacts, update_project_status, save_artifact

st.set_page_config(page_title="Pipeline — I-SCEET", page_icon="⚙️", layout="wide")
st.title("⚙️ Pipeline M1 → M6")
st.divider()

active = st.session_state.get("active_project")
if not active:
    st.warning("⚠️ Aucun projet actif. Retournez sur **1 Upload**.")
    st.stop()

st.markdown(f"**Projet actif :** {active['name']} — DAL {active['dal_level']}")
st.divider()

MODULES = [
    {"id": "M1", "name": "HLR Generator",          "model": "Qwen 2.5 24B Instruct",   "output": "SRD-001"},
    {"id": "M2", "name": "LLR Generator",           "model": "Mistral Small 24B",        "output": "SDDD-001"},
    {"id": "M3", "name": "Code Generator",          "model": "Qwen 2.5-Coder 24B",      "output": "/src"},
    {"id": "M4", "name": "LLT Generator ★ indép.", "model": "Gemma 3 27B",              "output": "SVCP-LLT-001"},
    {"id": "M5", "name": "HLT Generator ★ indép.", "model": "DeepSeek-R1 32B",          "output": "SVCP-HLT-001"},
    {"id": "M6", "name": "Traceability Generator",  "model": "Phi-4 14B",               "output": "STD-001"},
]

# ── COLAB STATUS ──────────────────────────────────────────────────────────────
st.markdown("### Connexion Colab")
colab_url = st.text_input("URL Colab (ngrok)", placeholder="https://xxxx.ngrok.io",
                          value=st.session_state.get("colab_url", ""))
if colab_url:
    st.session_state["colab_url"] = colab_url

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔗 Tester la connexion"):
        if colab_url:
            st.info("⏳ Test de connexion... (disponible quand Colab est actif)")
        else:
            st.error("Entrez l'URL ngrok d'abord.")
with col2:
    if not colab_url:
        st.warning("⚠️ URL Colab non configurée — pipeline en mode simulation")

st.divider()

# ── PIPELINE STATUS ───────────────────────────────────────────────────────────
st.markdown("### Statut des modules")
artifacts = get_artifacts(active["id"])
done_modules = {a["module"]: a for a in artifacts if a["module"] in
                [m["id"] for m in MODULES]}

for m in MODULES:
    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
    done = m["id"] in done_modules
    with col1:
        st.markdown("✅" if done else "⬜")
    with col2:
        st.markdown(f"**{m['id']}** — {m['name']}")
    with col3:
        st.caption(m["model"])
    with col4:
        st.caption(f"→ {m['output']}")

st.divider()

# ── RUN PIPELINE ──────────────────────────────────────────────────────────────
st.markdown("### Lancer le pipeline")
col1, col2 = st.columns(2)

with col1:
    mode = st.radio("Mode d'exécution", ["🚀 AUTO (M1→M6 complet)", "🔧 MANUEL (module par module)"])

with col2:
    st.markdown("**Mode AUTO** : génère M1→M6 sans interruption (~1h)")
    st.markdown("**Mode MANUEL** : tu valides avant chaque module suivant")

st.divider()

if "AUTO" in mode:
    if st.button("▶️ Lancer pipeline AUTO", type="primary"):
        if not colab_url:
            st.warning("⚠️ Mode simulation — Colab non connecté")
            progress = st.progress(0)
            status_text = st.empty()
            for i, m in enumerate(MODULES):
                status_text.markdown(f"⏳ Simulation {m['id']} — {m['name']}...")
                time.sleep(1)
                save_artifact(active["id"], m["id"], m["output"],
                              f"[SIMULATION] Output de {m['id']} — {m['name']}", "")
                progress.progress((i + 1) / len(MODULES))
            update_project_status(active["id"], "complete")
            status_text.markdown("✅ Simulation terminée !")
            st.success("Pipeline simulé. Allez sur **3 Revue** pour voir les outputs.")
        else:
            st.info("🔌 Connexion Colab active — pipeline réel disponible après configuration des modèles.")
else:
    st.markdown("**Sélectionner le module à exécuter :**")
    module_choice = st.selectbox("Module", [m["id"] + " — " + m["name"] for m in MODULES])
    if st.button("▶️ Lancer ce module", type="primary"):
        m_id = module_choice.split(" — ")[0]
        m = next(m for m in MODULES if m["id"] == m_id)
        with st.spinner(f"Exécution {m_id}..."):
            time.sleep(1)
            save_artifact(active["id"], m["id"], m["output"],
                          f"[SIMULATION] Output de {m['id']} — {m['name']}", "")
        st.success(f"✅ {m_id} terminé — output sauvegardé.")
        st.info("Validez puis passez au module suivant.")
