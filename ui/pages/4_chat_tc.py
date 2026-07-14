"""
================================================================================
 I-SCEET — Workspace 04 : Consultation des artefacts
 File: ui/pages/4_chat_tc.py
================================================================================
 Consultative-only chat over the generated engineering corpus.
 The page keeps the engineering baseline read-only and delegates answers to
 PCPipeline.chat() / M6 (Phi-4) when the Colab runtime is connected.
================================================================================
"""

import html
import os
import re
import sys

import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from Backend.db import (
    get_artifacts,
    get_chat_history,
    get_project_runtime_value,
    save_chat,
)
from orchestrator.pc_pipeline import PCPipeline
from theme import inject_theme, page_header


def _format_chat_text(value):
    '''Return safe, readable HTML for consultative chat content.'''
    text = html.escape(str(value or ""))
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r'<strong style="color:#182231 !important;-webkit-text-fill-color:#182231 !important;font-weight:700;">\1</strong>',
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"(?<!\*)\*([^*\n]+?)\*(?!\*)",
        r'<em style="color:#182231 !important;-webkit-text-fill-color:#182231 !important;">\1</em>',
        text,
    )
    return text.replace("\n", "<br>")


def _build_chat_message_html(role, content, target=None):
    """Build a theme-independent chat card with explicit dark text."""
    is_user = role == "user"
    label = "Vous" if is_user else "Assistant I-SCEET"
    icon = "◉" if is_user else "✦"
    accent = "#E4343A" if is_user else "#D97706"
    background = "#F3F4F6" if is_user else "#FFFFFF"
    border = "#D7DEE7" if is_user else "#E0E6ED"

    prefix = ""
    if target:
        safe_target = html.escape(str(target))
        prefix = (
            '<span style="display:inline-block;margin-right:.45rem;color:#52657B !important;'
            '-webkit-text-fill-color:#52657B !important;font-weight:700;">'
            f'[{safe_target}]</span>'
        )

    body = _format_chat_text(content)
    return f'''
        <div data-isc-chat-card="{role}" style="display:flex;gap:.78rem;align-items:flex-start;margin:.72rem 0 1rem 0;">
          <div style="flex:0 0 30px;width:30px;height:30px;border-radius:9px;background:{accent};
                      color:#FFFFFF !important;-webkit-text-fill-color:#FFFFFF !important;
                      display:flex;align-items:center;justify-content:center;font-weight:800;line-height:1;">
            {icon}
          </div>
          <div style="flex:1;min-width:0;background:{background};border:1px solid {border};border-radius:14px;
                      padding:.9rem 1rem;box-shadow:0 4px 12px rgba(15,29,44,.035);">
            <div style="color:#64748B !important;-webkit-text-fill-color:#64748B !important;
                        font-size:.72rem;font-weight:700;margin-bottom:.38rem;">{label}</div>
            <div data-isc-chat-text="true" style="color:#182231 !important;-webkit-text-fill-color:#182231 !important;
                        opacity:1 !important;font-size:.92rem;line-height:1.62;white-space:normal;">
              {prefix}{body}
            </div>
          </div>
        </div>
    '''


def _render_chat_message(role, content, target=None):
    st.markdown(
        _build_chat_message_html(role, content, target),
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Consultation — I-SCEET", layout="wide")
inject_theme()

# Page-local rules: keep the consultation workspace compact and guarantee
# readable chat content regardless of browser/Streamlit theme inheritance.
st.markdown(
    """
    <style>
      main .block-container {
        max-width: 1180px !important;
        padding-bottom: 7.5rem !important;
      }

      .isc-consult-intro {
        color: #52657B;
        font-size: .88rem;
        line-height: 1.55;
        margin: -.25rem 0 1rem;
      }

      .isc-consult-meta {
        display: flex;
        align-items: center;
        gap: .55rem;
        flex-wrap: wrap;
        margin: .15rem 0 .9rem;
      }

      .isc-consult-pill {
        display: inline-flex;
        align-items: center;
        min-height: 30px;
        padding: .32rem .7rem;
        border-radius: 999px;
        background: #F3F6F9;
        border: 1px solid #DCE4EC;
        color: #435267 !important;
        -webkit-text-fill-color: #435267 !important;
        font-size: .75rem;
        font-weight: 600;
      }

      .isc-consult-section {
        color: #5E6F84;
        font-family: 'Manrope', sans-serif;
        font-size: .7rem;
        font-weight: 800;
        letter-spacing: .14em;
        text-transform: uppercase;
        margin: 1rem 0 .6rem;
      }

      /* Chat cards */
      [data-testid='stChatMessage'] {
        background: #FFFFFF !important;
        color: #182231 !important;
        border: 1px solid #DCE4EC !important;
        border-radius: 16px !important;
        box-shadow: 0 6px 18px rgba(15,29,44,.035) !important;
        padding: .2rem .35rem !important;
        margin-bottom: .7rem !important;
      }

      [data-testid='stChatMessage'] [data-testid='stMarkdownContainer'],
      [data-testid='stChatMessage'] [data-testid='stMarkdownContainer'] p,
      [data-testid='stChatMessage'] [data-testid='stMarkdownContainer'] span,
      [data-testid='stChatMessage'] [data-testid='stMarkdownContainer'] div,
      [data-testid='stChatMessage'] [data-testid='stMarkdownContainer'] strong,
      [data-testid='stChatMessage'] [data-testid='stMarkdownContainer'] em,
      [data-testid='stChatMessage'] [data-testid='stMarkdownContainer'] li,
      [data-testid='stChatMessage'] [data-testid='stMarkdownContainer'] a {
        color: #182231 !important;
        -webkit-text-fill-color: #182231 !important;
        opacity: 1 !important;
      }

      [data-testid='stChatMessage'] [data-testid='stMarkdownContainer'] p {
        line-height: 1.62 !important;
      }

      [data-testid='stChatMessage'] [data-testid='stMarkdownContainer'] code,
      [data-testid='stChatMessage'] [data-testid='stMarkdownContainer'] pre {
        color: #182231 !important;
        -webkit-text-fill-color: #182231 !important;
        background: #F3F6F9 !important;
        border-color: #DCE4EC !important;
      }

      /* Chat input: light, readable, and visually integrated with the page. */
      [data-testid='stChatInput'],
      [data-testid='stChatInput'] > div,
      [data-testid='stChatInput'] [data-baseweb='textarea'],
      [data-testid='stChatInput'] [data-baseweb='base-input'] {
        background: #FFFFFF !important;
        color: #111827 !important;
        border-color: #C9D5E2 !important;
      }

      [data-testid='stChatInput'] textarea,
      [data-testid='stChatInputTextArea'] {
        background: #FFFFFF !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        caret-color: #111827 !important;
        opacity: 1 !important;
      }

      [data-testid='stChatInput'] textarea::placeholder,
      [data-testid='stChatInputTextArea']::placeholder {
        color: #77869A !important;
        -webkit-text-fill-color: #77869A !important;
        opacity: 1 !important;
      }

      [data-testid='stBottomBlockContainer'],
      [data-testid='stBottom'],
      .stBottom {
        background: rgba(246,248,251,.96) !important;
        backdrop-filter: blur(10px);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

page_header(
    "WORKSPACE 04 • CONSULTATION",
    "Consultation des artefacts",
    "Interrogez le corpus d'ingénierie généré sans modifier la baseline ni les artefacts approuvés.",
)

st.markdown(
    '<div class="isc-consult-intro">'
    "Le modèle consultatif analyse les sorties disponibles du pipeline. "
    "Cette page est strictement en lecture seule."
    "</div>",
    unsafe_allow_html=True,
)

active = st.session_state.get("active_project")
if not active:
    st.warning("Aucun projet actif. Activez d'abord un projet dans le workspace 01 ou 06.")
    st.stop()

artifacts = get_artifacts(active["id"])

# Keep one representative artefact per module. Prefer the row carrying the
# richest textual content so empty DD/CT registration rows are never selected.
module_artifacts = {}
for artifact_row in artifacts:
    module = artifact_row.get("module")
    if module not in {"M1", "M2", "M3", "M4", "M5", "M6"}:
        continue
    current = module_artifacts.get(module)
    if current is None or len(artifact_row.get("content") or "") > len(current.get("content") or ""):
        module_artifacts[module] = artifact_row

if not module_artifacts:
    st.info("Aucun artefact généré. Lancez d'abord le pipeline.")
    st.stop()

colab_url = (
    st.session_state.get(f"colab_url_project_{active['id']}")
    or get_project_runtime_value(active["id"], "colab_url", "")
    or st.session_state.get("colab_url", "")
)
if colab_url:
    st.session_state[f"colab_url_project_{active['id']}"] = colab_url
    st.session_state["colab_url"] = colab_url

# Compact consultation context.
left, right = st.columns([1.05, 2.15], vertical_alignment="bottom")
with left:
    target_options = list(module_artifacts.keys()) + ["ALL"]
    target = st.selectbox(
        "Artefacts à interroger",
        target_options,
        format_func=lambda value: "ALL — Tous les modules" if value == "ALL" else value,
    )

with right:
    if target == "ALL":
        target_detail = f"{len(module_artifacts)} modules disponibles"
    else:
        selected_artifact = module_artifacts[target]
        target_detail = (
            f"{selected_artifact['type']} · "
            f"{len(selected_artifact.get('content') or ''):,} caractères"
        )

    runtime_state = "M6 connecté" if colab_url else "Mode simulation"
    safe_project_name = html.escape(str(active["name"]))
    safe_target = html.escape(str(target))
    safe_target_detail = html.escape(str(target_detail))
    safe_runtime_state = html.escape(runtime_state)
    st.markdown(
        '<div class="isc-consult-meta">'
        f'<span class="isc-consult-pill">Projet · {safe_project_name}</span>'
        f'<span class="isc-consult-pill">Cible · {safe_target}</span>'
        f'<span class="isc-consult-pill">{safe_target_detail}</span>'
        f'<span class="isc-consult-pill">{safe_runtime_state}</span>'
        "</div>",
        unsafe_allow_html=True,
    )

history = get_chat_history(active["id"])

if history:
    history_head, history_control = st.columns([3, 1], vertical_alignment="center")
    with history_head:
        st.markdown('<div class="isc-consult-section">Conversation récente</div>', unsafe_allow_html=True)
    with history_control:
        show_all_history = st.toggle(
            "Tout afficher",
            value=False,
            key="consultation_show_all_history",
            help="Affiche tout l'historique de consultation du projet.",
        )

    visible_history = history if show_all_history else history[-4:]
    if not show_all_history and len(history) > len(visible_history):
        st.caption(
            f"{len(visible_history)} derniers échanges affichés sur {len(history)}. "
            "Activez « Tout afficher » pour consulter l'historique complet."
        )

    for item in visible_history:
        _render_chat_message("user", item["question"], item["target"])
        _render_chat_message("assistant", item["answer"])
else:
    st.markdown('<div class="isc-consult-section">Nouvelle consultation</div>', unsafe_allow_html=True)
    st.info("Aucun échange enregistré pour ce projet. Posez votre première question ci-dessous.")

question = st.chat_input("Posez votre question sur les artefacts…")

if question:
    _render_chat_message("user", question, target)

    if not colab_url:
        answer = (
            "**Mode simulation — Colab non connecté**\n\n"
            f"Question reçue pour **{target}** : *{question}*\n\n"
            "Connectez le runtime Colab depuis **02 Pipeline M1 → M6** "
            "pour obtenir une réponse du modèle consultatif."
        )
    else:
        with st.spinner("M6 analyse les artefacts…"):
            pipeline = PCPipeline(colab_url, active["id"])
            chat_artifacts = {
                module: artifact_row.get("content", "")
                for module, artifact_row in module_artifacts.items()
            }
            result = pipeline.chat(target, question, chat_artifacts)

        if result.get("status") == "success":
            answer = result.get("answer", "(réponse vide)")
        else:
            answer = f"Erreur — {result.get('answer', 'Erreur inconnue')}"

    _render_chat_message("assistant", answer)
    save_chat(active["id"], target, question, answer)

st.caption(
    "Consultation uniquement : pour corriger un artefact, utilisez le workspace "
    "05 Technical comments puis relancez le module concerné."
)
