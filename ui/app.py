"""
================================================================================
 I-SCEET — Accueil
 File: ui/app.py
================================================================================
"""

import streamlit as st
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Backend.db import get_all_projects, get_artifacts, get_reviews, get_tc_remarks

st.set_page_config(page_title="I-SCEET", page_icon="✈️", layout="wide")

# ── STYLE ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.iscet-hero {
    background: linear-gradient(135deg, #0B1F3A 0%, #1F3864 55%, #2E5C8A 100%);
    border-radius: 14px;
    padding: 2.6rem 2.4rem;
    margin-bottom: 1.6rem;
    color: #FFFFFF;
    position: relative;
    overflow: hidden;
    border: 1px solid #3B5A85;
}
.iscet-hero::after {
    content: "";
    position: absolute; top: -40px; right: -40px;
    width: 220px; height: 220px; border-radius: 50%;
    background: radial-gradient(circle, rgba(255,193,7,0.18) 0%, rgba(255,193,7,0) 70%);
}
.iscet-hero h1 {
    font-size: 2.3rem; margin-bottom: 0.2rem; font-weight: 800;
    letter-spacing: 0.5px;
}
.iscet-hero .tagline {
    font-size: 1.05rem; color: #DCE6F1; font-weight: 400;
}
.iscet-hero .badges { margin-top: 1rem; }
.iscet-badge {
    display: inline-block; background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,193,7,0.5); color: #FFC107;
    border-radius: 20px; padding: 0.25rem 0.9rem; margin-right: 0.5rem;
    font-size: 0.78rem; font-weight: 600; letter-spacing: 0.4px;
}
.iscet-card {
    border: 1px solid #E3E8EF; border-radius: 12px; padding: 1.1rem 1.2rem;
    height: 100%; transition: 0.15s; background: #FFFFFF;
}
.iscet-card:hover { border-color: #2E75B6; box-shadow: 0 2px 10px rgba(46,117,182,0.12); }
.iscet-card .icon { font-size: 1.6rem; }
.iscet-card h4 { margin: 0.3rem 0 0.2rem 0; color: #1F3864; }
.iscet-card p { color: #667; font-size: 0.85rem; margin: 0; }
.pipeline-dot { font-size: 1.3rem; }
</style>
""", unsafe_allow_html=True)

# ── HERO ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="iscet-hero">
  <h1>✈️ I-SCEET</h1>
  <div class="tagline">Intelligent Safety-Critical Engineering Environment Toolchain</div>
  <div class="tagline">AI-driven, fully-traceable DO-178C DAL A software certification pipeline —
  from requirements to code to verification, for engine-control-class embedded systems.</div>
  <div class="badges">
    <span class="iscet-badge">DO-178C</span>
    <span class="iscet-badge">ARP4754A</span>
    <span class="iscet-badge">DAL A</span>
    <span class="iscet-badge">MC/DC 100%</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── ACTIVE PROJECT OVERVIEW ────────────────────────────────────────────────
active = st.session_state.get("active_project")
all_projects = get_all_projects()

if active:
    artifacts = get_artifacts(active["id"])
    reviews = get_reviews(active["id"])
    tc = get_tc_remarks(active["id"])
    modules_done = {a["module"] for a in artifacts if a["module"] in
                    ["M1", "M2", "M3", "M4", "M5", "M6"]}

    st.markdown(f"### 🛫 Active project: `{active['name']}` — DAL {active['dal_level']}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pipeline", f"{len(modules_done)}/6 modules")
    c2.metric("✅ Approved", sum(1 for r in reviews if r["status"] == "approved"))
    c3.metric("🔴 Open remarks", sum(1 for t in tc if t["status"] == "open"))
    c4.metric("Status", active.get("status", "in_progress"))

    st.markdown("**Pipeline progress:**")
    cols = st.columns(6)
    for i, m in enumerate(["M1", "M2", "M3", "M4", "M5", "M6"]):
        with cols[i]:
            icon = "✅" if m in modules_done else "⬜"
            st.markdown(f"<div class='pipeline-dot'>{icon}</div>{m}", unsafe_allow_html=True)

    bcol1, bcol2 = st.columns(2)
    with bcol1:
        st.page_link("pages/2_pipeline.py", label="Continue pipeline", icon="⚙️")
    with bcol2:
        st.page_link("pages/3_revue.py", label="Review artifacts", icon="🔍")
else:
    st.info(
        f"No active project selected. "
        f"{'Pick one from **Historique**, or ' if all_projects else ''}"
        f"start a **New project** below."
    )

st.divider()

# ── NAVIGATION ──────────────────────────────────────────────────────────────
st.markdown("### Navigate")

NAV = [
    ("pages/1_upload.py", "📤", "New project / Upload",
     "Create a project and upload PDS, Architecture, Hardware docs, and the 9 planning/standards documents."),
    ("pages/2_pipeline.py", "⚙️", "Pipeline M1 → M6",
     "Connect to Colab and run the AI pipeline: HLR, LLR, code, tests, traceability."),
    ("pages/3_revue.py", "🔍", "Review artifacts",
     "Inspect every generated artifact (SRD, SDDD, DD, CT, /src, SUTC, SVTC, TM) and approve or flag for revision."),
    ("pages/4_chat_tc.py", "💬", "Consultative chat",
     "Ask questions about generated artifacts — consultative only, does not modify outputs."),
    ("pages/5_tc_excel.py", "📊", "Technical comments",
     "Log remarks, send them to the responsible AI module for resolution, and confirm the fix."),
    ("pages/6_historique.py", "📁", "Project history",
     "Browse, reactivate, or delete past projects and see their full generation history."),
]

for row_start in range(0, len(NAV), 3):
    cols = st.columns(3)
    for col, (page, icon, title, desc) in zip(cols, NAV[row_start:row_start + 3]):
        with col:
            st.markdown(f"""
            <div class="iscet-card">
                <div class="icon">{icon}</div>
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link(page, label="Open", icon="➡️")
            st.write("")

st.divider()
st.caption(
    "I-SCEET — validation test project: "
    "STM32F303VCT6 bootloader + drivers for a FADEC-class engine control unit."
)