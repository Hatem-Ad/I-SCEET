"""I-SCEET — Homepage V8 aligned with the approved aerospace mockup."""

import os
import sys
import textwrap
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Backend.db import get_all_projects, get_artifacts, get_reviews, get_tc_remarks
from theme import inject_theme, module_rail, metric_card, action_card

st.set_page_config(page_title="I-SCEET", page_icon="✈️", layout="wide")
inject_theme()

# The active project is resolved centrally by inject_theme(): session state is
# refreshed first, then the last explicitly activated project is restored from SQLite.
active = st.session_state.get("active_project")
projects = get_all_projects()
artifacts = get_artifacts(active["id"]) if active else []
reviews = get_reviews(active["id"]) if active else []
tc = get_tc_remarks(active["id"]) if active else []
modules_done = {a["module"] for a in artifacts if a.get("module") in {"M1", "M2", "M3", "M4", "M5", "M6"}}

badges = ""
if active:
    badges = textwrap.dedent(
        f"""
        <div style='display:flex;gap:.65rem;flex-wrap:wrap;position:absolute;right:1.9rem;top:1.7rem;z-index:2'>
          <div class='isc-dal-badge'><div class='lbl'>Project</div><div class='val' style='font-size:.9rem;max-width:180px'>{active['name']}</div></div>
          <div class='isc-dal-badge'><div class='lbl'>DAL</div><div class='val'>{active['dal_level']}</div></div>
        </div>
        """
    ).strip()

st.markdown(
    textwrap.dedent(
        """
        <div class='isc-topbar'>

          <div class='isc-topbar-right'>



          </div>
        </div>
        """
    ),
    unsafe_allow_html=True,
)

st.markdown(
    textwrap.dedent(
        f"""
        <div class='isc-hero'>
          {badges}
          <div class='isc-hero-content'>
            <div class='isc-kicker'>Aerospace Digital Engineering Platform</div>
            <div class='isc-hero-title'>Engineering assurance,<br>from requirement to evidence<span class='dot'>.</span></div>
            <div class='isc-hero-rule'></div>
            <div class='isc-hero-tag'>
              I-SCEET orchestrates AI-assisted generation, review, baselining and traceability for DO-178C lifecycle artefacts.
              The platform is designed for disciplined, reviewable and versioned engineering workflows.
            </div>
            <div class='isc-product-name'>I-SCEET — Intelligent Safety-Critical Engineering Environment Toolchain</div>
          </div>
        </div>
        """
    ),
    unsafe_allow_html=True,
)

module_rail(
    modules_done,
    label=(f"Delivery pipeline — {active['name']}" if active else "Delivery pipeline — no active project"),
)

m1, m2, m3, m4 = st.columns(4, gap="medium")
with m1:
    metric_card("projects", "red", "Projects", str(len(projects)), "Total projects")
with m2:
    metric_card("pipeline", "blue", "Pipeline completion", f"{len(modules_done)}/6" if active else "0/6", "Modules completed")
with m3:
    approved = sum(1 for review in reviews if review.get("status") == "approved")
    metric_card("reviews", "green", "Approved reviews", str(approved), "Baselines approved")
with m4:
    open_tc = sum(1 for remark in tc if remark.get("status") == "open")
    metric_card("comments", "amber", "Open technical comments", str(open_tc), "Pending actions")

st.markdown("<div class='isc-section-title' style='margin-top:1.25rem'>Primary actions</div>", unsafe_allow_html=True)
a1, a2, a3 = st.columns(3, gap="medium")
with a1:
    action_card("folder", "red", "Configure project inputs", "Create a project and upload all required engineering inputs.", "./upload")
with a2:
    action_card("rocket", "blue", "Run M1 → M6 pipeline", "Execute the full generation pipeline from M1 to M6.", "./pipeline")
with a3:
    action_card("review", "green", "Review generated artefacts", "Inspect, review and compare generated artefacts and baselines.", "./revue")

b1, b2, b3 = st.columns(3, gap="medium")
with b1:
    action_card("consultation", "blue", "Ask a consultative question", "Query generated artefacts without modifying the engineering baseline.", "./chat_tc")
with b2:
    action_card("comments", "amber", "Manage technical comments", "Register, track and relaunch corrective actions from technical remarks.", "./tc_excel")
with b3:
    action_card("history", "green", "Browse configuration history", "Inspect projects, baselines, lifecycle history and released versions.", "./historique")