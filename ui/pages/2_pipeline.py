"""
================================================================================
 I-SCEET — Page 2 : Pipeline M1→M6
 File: ui/pages/2_pipeline.py
 Copyright (c) 2026 Hatem Adouani — MIT License
================================================================================
 v2: fixed stale artifact names (SVCP-LLT/HLT-001 -> SUTC/SVTC, STD-001 ->
 TM), M2 now shown with its 3 outputs (SDDD/DD/CT), and progress_callback
 is actually wired to pc_pipeline.py's live /progress polling instead of
 a static spinner - both AUTO and MANUAL mode show real stage messages
 (loading model / generating / unloading) as they happen.
================================================================================
"""

import streamlit as st
import sys, os, time, textwrap

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Backend.db import (
    get_artifacts,
    update_project_status,
    get_project_runtime_value,
    set_project_runtime_value,
)
from orchestrator.pc_pipeline import PCPipeline
from theme import inject_theme, page_header, module_rail, badge, LINE, TEXT_900

st.set_page_config(page_title="Pipeline — I-SCEET", layout="wide")
inject_theme()
page_header("WORKSPACE 02 • PIPELINE", "Pipeline M1 \u2192 M6")

active = st.session_state.get("active_project")
if not active:
    st.markdown(
    """
    <div style="
        background-color: #FFFBD6;
        color: #111827;
        border: 1px solid #F0E7A0;
        border-radius: 10px;
        padding: 0.9rem 1rem;
        font-size: 0.95rem;
        font-weight: 500;
    ">
        Aucun projet actif. Rendez-vous sur <strong>1 Upload</strong> d'abord.
    </div>
    """,
    unsafe_allow_html=True,
)
    st.stop()

st.markdown(f"**Projet :** {active['name']} \u2014 DAL {active['dal_level']}")
st.page_link("pages/1_upload.py", label="Modifier les documents d'input de ce projet")
st.divider()

MODULES = [
    {"id": "M1", "name": "HLR Generator",           "model": "Qwen3 32B",         "outputs": ["SRD"]},
    {"id": "M2", "name": "LLR Generator",            "model": "Mistral Small 24B", "outputs": ["SDDD", "DD", "CT"]},
    {"id": "M3", "name": "Code Generator",           "model": "Qwen2.5-Coder 32B", "outputs": ["SRC"]},
    {"id": "M4", "name": "LLT Generator ★ indep.",   "model": "Gemma3 27B",        "outputs": ["SUTC"]},
    {"id": "M5", "name": "HLT Generator ★ indep.",   "model": "DeepSeek-R1 32B",   "outputs": ["SVTC"]},
    {"id": "M6", "name": "Traceability Generator",   "model": "Phi-4 14B",         "outputs": ["TM"]},
]

# ── COLAB CONNECTION ──────────────────────────────────────────────────────────
st.markdown('<div class="isc-eyebrow">Connexion Colab</div>', unsafe_allow_html=True)

from dotenv import load_dotenv
load_dotenv()
# The Colab endpoint is configured only through COLAB_URL in .env
# (see .env.example) - no endpoint is hard-coded in the repository.
env_url = os.getenv("COLAB_URL", "").strip()

project_url_key = f"colab_url_project_{active['id']}"
persisted_url = get_project_runtime_value(active["id"], "colab_url", "")
stored_url = (
    st.session_state.get(project_url_key)
    or persisted_url
    or env_url
)

if not env_url:
    st.error(
        "COLAB_URL is not set. Copy `.env.example` to `.env`, set `COLAB_URL` "
        "to the public URL of your Colab inference server (e.g. your ngrok "
        "domain), then restart the app."
    )

colab_url = st.text_input(
    "Colab URL (ngrok)",
    placeholder="Set COLAB_URL in .env",
    value=stored_url,
    key=f"colab_url_input_{active['id']}",
).strip()

# Keep the same endpoint available in Pipeline, Consultation and TC pages,
# including after a browser refresh or a reverse-proxy reconnect.
if colab_url:
    st.session_state[project_url_key] = colab_url
    st.session_state["colab_url"] = colab_url  # backward compatibility
    if colab_url != persisted_url:
        set_project_runtime_value(active["id"], "colab_url", colab_url)

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Tester la connexion"):
        if colab_url:
            with st.spinner("Test en cours..."):
                pipeline = PCPipeline(colab_url, active["id"], active["name"])
                status = pipeline.test_connection()
            if status.get("status") == "online":
                st.markdown(badge(f"En ligne \u2014 GPU: {status.get('gpu_name', 'N/A')}", "success"), unsafe_allow_html=True)
                st.session_state[f"colab_connected_{active['id']}"] = True
            else:
                st.markdown(badge(f"Hors ligne \u2014 {status.get('error', 'Inconnu')}", "danger"), unsafe_allow_html=True)
                st.session_state[f"colab_connected_{active['id']}"] = False
        else:
            st.error("Entrez d'abord l'URL ngrok.")
with col2:
    if st.session_state.get(f"colab_connected_{active['id']}"):
        st.markdown(badge("Colab connect\u00e9 et pr\u00eat", "success"), unsafe_allow_html=True)
    else:
        st.markdown(badge("Colab non connect\u00e9 \u2014 testez la connexion d'abord", "neutral"), unsafe_allow_html=True)

st.divider()

# ── PIPELINE STATUS ───────────────────────────────────────────────────────────
st.markdown('<div class="isc-eyebrow">Statut du pipeline</div>', unsafe_allow_html=True)
artifacts = get_artifacts(active["id"])
modules_done_full = set()

cols = st.columns(6)
for i, m in enumerate(MODULES):
    module_artifacts = {a["type"] for a in artifacts if a["module"] == m["id"]}
    all_present = all(out in module_artifacts for out in m["outputs"])
    if all_present:
        modules_done_full.add(m["id"])
    with cols[i]:
        badges_html = "".join(
            f"<div style='margin-top:.35rem'>{badge(out, 'success' if out in module_artifacts else 'neutral')}</div>"
            for out in m["outputs"]
        )
        st.markdown(
            textwrap.dedent(f"""
            <div style='background:#fff;border:1px solid {LINE};border-radius:14px;padding:.85rem .8rem;min-height:100%'>
              <div style="font-weight:700;color:{TEXT_900};margin-bottom:.2rem">{m['id']}</div>
              {badges_html}
            </div>
            """).strip(),
            unsafe_allow_html=True,
        )

module_rail(modules_done_full, label="", light=True)

st.divider()

# ── RUN PIPELINE ──────────────────────────────────────────────────────────────
st.markdown('<div class="isc-eyebrow">Lancer le pipeline</div>', unsafe_allow_html=True)
mode = st.radio("Mode", ["AUTO — M1→M6 complete", "MANUAL — module by module"])

if "AUTO" in mode:
    if st.button("Lancer le pipeline AUTO", type="primary"):
        if not colab_url:
            st.error("Entrez d'abord l'URL Colab.")
            st.stop()

        pipeline = PCPipeline(colab_url, active["id"], active["name"])
        progress_bar = st.progress(0)
        module_label = st.empty()
        live_status  = st.empty()
        all_results  = {}

        for i, m in enumerate(MODULES):
            mid = m["id"]
            module_label.markdown(f"**Running {mid} — {m['name']} ({m['model']})**")
            live_status.markdown("En cours de démarrage...")

            def make_callback(placeholder):
                def cb(module, message):
                    placeholder.markdown(message)
                return cb

            result = pipeline.run_single(mid, progress_callback=make_callback(live_status))
            all_results[mid] = result
            progress_bar.progress((i + 1) / len(MODULES))

            if result.get("status") == "error":
                live_status.error(f"{mid} en échec : {result.get('message')}")
                break
            else:
                live_status.success(
                    f"**{mid}** terminé — {', '.join(m['outputs'])} enregistré en base "
                    f"(v{result.get('version', '?')})"
                )
                time.sleep(0.3)

        success = sum(1 for r in all_results.values() if r.get("status") == "success")
        if success == len(MODULES):
            st.success("Pipeline terminé : les 6 modules ont été générés.")
            st.page_link("pages/3_revue.py", label="Aller à la revue")
            update_project_status(active["id"], "complete")
        else:
            st.warning(f"{success}/6 modules réussis.")

else:
    module_choice = st.selectbox(
        "Module", [f"{m['id']} — {m['name']}" for m in MODULES]
    )
    if st.button("Lancer ce module", type="primary"):
        if not colab_url:
            st.error("Entrez d'abord l'URL Colab.")
            st.stop()

        mid = module_choice.split(" — ")[0]
        pipeline = PCPipeline(colab_url, active["id"], active["name"])

        live_status = st.empty()
        live_status.markdown("En cours de démarrage...")

        def cb(module, message):
            live_status.markdown(message)

        result = pipeline.run_single(mid, progress_callback=cb)

        if result.get("status") == "success":
            live_status.success(
                f"{mid} terminé — enregistré en base (v{result.get('version', '?')})"
            )
            st.text_area(
                "Aperçu de la sortie (1000 premiers caractères)",
                result.get("output", "")[:1000],
                height=200
            )
            extra = result.get("extra_files") or {}
            if extra:
                st.caption(f"Artefacts supplémentaires : {', '.join(extra.keys())}")
            st.page_link("pages/3_revue.py", label="Aller à la revue")
        else:
            live_status.error(f"Erreur : {result.get('message', 'Inconnue')}")