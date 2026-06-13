"""
================================================================================
 I-SCEET — Page 2 : Pipeline M1→M6
 File: ui/pages/2_pipeline.py
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
    {"id": "M1", "name": "HLR Generator",          "model": "Qwen3 32B",          "output": "SRD-001"},
    {"id": "M2", "name": "LLR Generator",           "model": "Mistral Small 24B",  "output": "SDDD-001"},
    {"id": "M3", "name": "Code Generator",          "model": "Qwen2.5-Coder 32B", "output": "/src"},
    {"id": "M4", "name": "LLT Generator ★ indep.", "model": "Gemma3 27B",         "output": "SVCP-LLT-001"},
    {"id": "M5", "name": "HLT Generator ★ indep.", "model": "DeepSeek-R1 32B",    "output": "SVCP-HLT-001"},
    {"id": "M6", "name": "Traceability Generator",  "model": "Phi-4 14B",          "output": "STD-001"},
]

# ── COLAB CONNECTION ──────────────────────────────────────────────────────────
st.markdown("### 🔌 Colab Connection")
colab_url = st.text_input(
    "Colab URL (ngrok)",
    placeholder="https://xxxx.ngrok-free.app",
    value=st.session_state.get("colab_url", "")
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
artifacts    = get_artifacts(active["id"])
done_modules = {a["module"]: a for a in artifacts
                if a["module"] in [m["id"] for m in MODULES]}

cols = st.columns(6)
for i, m in enumerate(MODULES):
    done = m["id"] in done_modules
    with cols[i]:
        st.markdown("✅" if done else "⬜")
        st.markdown(f"**{m['id']}**")
        st.caption(m["output"])

st.divider()

# ── RUN PIPELINE ──────────────────────────────────────────────────────────────
st.markdown("### 🚀 Run Pipeline")
mode = st.radio("Mode", ["AUTO — M1→M6 complete", "MANUAL — module by module"])

if "AUTO" in mode:
    if st.button("▶️ Launch AUTO Pipeline", type="primary"):
        if not colab_url:
            st.error("Enter Colab URL first.")
            st.stop()

        pipeline     = PCPipeline(colab_url, active["id"])
        progress_bar = st.progress(0)
        status_text  = st.empty()
        all_results  = {}

        for i, m in enumerate(MODULES):
            mid = m["id"]
            status_text.markdown(
                f"⏳ Running **{mid}** — {m['name']} ({m['model']})..."
            )
            result = pipeline.run_single(mid)
            all_results[mid] = result
            progress_bar.progress((i + 1) / len(MODULES))

            if result.get("status") == "error":
                status_text.error(
                    f"❌ {mid} failed: {result.get('message')}"
                )
                break
            else:
                elapsed = result.get("elapsed", "?")
                status_text.markdown(
                    f"✅ **{mid}** done in {elapsed}s → {m['output']} saved to DB"
                )
                time.sleep(0.3)

        success = sum(1 for r in all_results.values()
                      if r.get("status") == "success")
        if success == len(MODULES):
            st.success("🎉 Pipeline complete! All 6 modules generated.")
            st.info("Go to **3 Revue** to review all outputs.")
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

        mid      = module_choice.split(" — ")[0]
        pipeline = PCPipeline(colab_url, active["id"])

        with st.spinner(f"Running {mid}... (may take several minutes)"):
            result = pipeline.run_single(mid)

        if result.get("status") == "success":
            st.success(
                f"✅ {mid} done in {result.get('elapsed', '?')}s — "
                f"saved to DB"
            )
            st.text_area(
                "Output preview (first 1000 chars)",
                result.get("output", "")[:1000],
                height=200
            )
            st.info("Go to **3 Revue** to see the full output.")
        else:
            st.error(f"❌ Error: {result.get('message', 'Unknown')}")
