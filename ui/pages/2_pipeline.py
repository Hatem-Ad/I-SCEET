"""
================================================================================
 I-SCEET — Page 2 : Pipeline M1→M6
 File: ui/pages/2_pipeline.py
================================================================================
 v2: fixed stale artifact names (SVCP-LLT/HLT-001 -> SUTC/SVTC, STD-001 ->
 TM), M2 now shown with its 3 outputs (SDDD/DD/CT), and progress_callback
 is actually wired to pc_pipeline.py's live /progress polling instead of
 a static spinner - both AUTO and MANUAL mode show real stage messages
 (loading model / generating / unloading) as they happen.
================================================================================
"""

import streamlit as st
import sys, os, time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from Backend.db import get_artifacts, update_project_status
from orchestrator.pc_pipeline import PCPipeline

st.set_page_config(page_title="Pipeline — I-SCEET", page_icon="⚙️", layout="wide")
st.title("⚙️ Pipeline M1 → M6")
st.divider()

active = st.session_state.get("active_project")
if not active:
    st.warning("⚠️ No active project. Go to **1 Upload** first.")
    st.stop()

st.markdown(f"**Project:** {active['name']} — DAL {active['dal_level']}")
st.divider()

MODULES = [
    {"id": "M1", "name": "HLR Generator",           "model": "Qwen3 32B",         "outputs": ["SRD"]},
    {"id": "M2", "name": "LLR Generator",            "model": "Mistral Small 24B", "outputs": ["SDDD", "DD", "CT"]},
    {"id": "M3", "name": "Code Generator",           "model": "Qwen2.5-Coder 32B", "outputs": ["/src"]},
    {"id": "M4", "name": "LLT Generator ★ indep.",   "model": "Gemma3 27B",        "outputs": ["SUTC"]},
    {"id": "M5", "name": "HLT Generator ★ indep.",   "model": "DeepSeek-R1 32B",   "outputs": ["SVTC"]},
    {"id": "M6", "name": "Traceability Generator",   "model": "Phi-4 14B",         "outputs": ["TM"]},
]

# ── COLAB CONNECTION ──────────────────────────────────────────────────────────
st.markdown("### 🔌 Colab Connection")

from dotenv import load_dotenv
load_dotenv()
default_url = os.getenv("COLAB_URL", "")

colab_url = st.text_input(
    "Colab URL (ngrok)",
    placeholder="https://xxxx.ngrok-free.app",
    value=st.session_state.get("colab_url", default_url)
)
if colab_url:
    st.session_state["colab_url"] = colab_url

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔗 Test Connection"):
        if colab_url:
            with st.spinner("Testing..."):
                pipeline = PCPipeline(colab_url, active["id"])
                status = pipeline.test_connection()
            if status.get("status") == "online":
                st.success(f"✅ Online — GPU: {status.get('gpu_name', 'N/A')}")
                st.session_state["colab_connected"] = True
            else:
                st.error(f"❌ Offline — {status.get('error', 'Unknown')}")
                st.session_state["colab_connected"] = False
        else:
            st.error("Enter ngrok URL first.")
with col2:
    if st.session_state.get("colab_connected"):
        st.success("✅ Colab connected and ready")
    else:
        st.warning("⚠️ Colab not connected — test connection first")

st.divider()

# ── PIPELINE STATUS ───────────────────────────────────────────────────────────
st.markdown("### 📊 Pipeline Status")
artifacts = get_artifacts(active["id"])

cols = st.columns(6)
for i, m in enumerate(MODULES):
    module_artifacts = {a["type"] for a in artifacts if a["module"] == m["id"]}
    with cols[i]:
        st.markdown(f"**{m['id']}**")
        for out in m["outputs"]:
            done = out in module_artifacts
            st.markdown(f"{'✅' if done else '⬜'} {out}")

st.divider()

# ── RUN PIPELINE ──────────────────────────────────────────────────────────────
st.markdown("### 🚀 Run Pipeline")
mode = st.radio("Mode", ["AUTO — M1→M6 complete", "MANUAL — module by module"])

if "AUTO" in mode:
    if st.button("▶️ Launch AUTO Pipeline", type="primary"):
        if not colab_url:
            st.error("Enter Colab URL first.")
            st.stop()

        pipeline = PCPipeline(colab_url, active["id"])
        progress_bar = st.progress(0)
        module_label = st.empty()
        live_status  = st.empty()
        all_results  = {}

        for i, m in enumerate(MODULES):
            mid = m["id"]
            module_label.markdown(f"**Running {mid} — {m['name']} ({m['model']})**")
            live_status.markdown("⏳ Starting...")

            def make_callback(placeholder):
                def cb(module, message):
                    placeholder.markdown(message)
                return cb

            result = pipeline.run_single(mid, progress_callback=make_callback(live_status))
            all_results[mid] = result
            progress_bar.progress((i + 1) / len(MODULES))

            if result.get("status") == "error":
                live_status.error(f"❌ {mid} failed: {result.get('message')}")
                break
            else:
                live_status.success(
                    f"✅ **{mid}** done — {', '.join(m['outputs'])} saved to DB "
                    f"(v{result.get('version', '?')})"
                )
                time.sleep(0.3)

        success = sum(1 for r in all_results.values() if r.get("status") == "success")
        if success == len(MODULES):
            st.success("🎉 Pipeline complete! All 6 modules generated.")
            st.page_link("pages/3_revue.py", label="Go to Revue", icon="🔍")
            update_project_status(active["id"], "complete")
        else:
            st.warning(f"⚠️ {success}/6 modules succeeded.")

else:
    module_choice = st.selectbox(
        "Module", [f"{m['id']} — {m['name']}" for m in MODULES]
    )
    if st.button("▶️ Run this module", type="primary"):
        if not colab_url:
            st.error("Enter Colab URL first.")
            st.stop()

        mid = module_choice.split(" — ")[0]
        pipeline = PCPipeline(colab_url, active["id"])

        live_status = st.empty()
        live_status.markdown("⏳ Starting...")

        def cb(module, message):
            live_status.markdown(message)

        result = pipeline.run_single(mid, progress_callback=cb)

        if result.get("status") == "success":
            live_status.success(
                f"✅ {mid} done — saved to DB (v{result.get('version', '?')})"
            )
            st.text_area(
                "Output preview (first 1000 chars)",
                result.get("output", "")[:1000],
                height=200
            )
            extra = result.get("extra_files") or {}
            if extra:
                st.caption(f"Additional artifacts: {', '.join(extra.keys())}")
            st.page_link("pages/3_revue.py", label="Go to Revue", icon="🔍")
        else:
            live_status.error(f"❌ Error: {result.get('message', 'Unknown')}")