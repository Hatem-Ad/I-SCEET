"""
================================================================================
 I-SCEET — Système de conception (Design System)
 File: ui/theme.py
================================================================================
 Habillage visuel partagé par toutes les pages. Aucune logique métier ici :
 uniquement des tokens de style et des composants d'affichage réutilisables.
 Direction : marine institutionnelle (#141d29) + accent
 ambre technique (instrumentation aéronautique), typographie IBM Plex.
================================================================================
"""

import streamlit as st
import textwrap

# ── TOKENS ──────────────────────────────────────────────────────────────────
INK_900     = "#0A1420"   # fond hero / bandeaux sombres
INK_700     = "#16233A"
LINE_INK    = "#1D2C40"   # séparateurs sur fond sombre
STEEL_400   = "#8FA3B8"   # texte secondaire sur fond sombre
STEEL_600   = "#5C7189"   # texte tertiaire sur fond sombre

PAPER       = "#F5F6F8"   # fond de page
CARD        = "#FFFFFF"
LINE        = "#DDE2E8"   # séparateurs sur fond clair
TEXT_900    = "#0F1720"   # texte principal
TEXT_600    = "#5B6672"   # texte secondaire

ACCENT      = "#C6912B"   # ambre technique — accent unique de la marque
ACCENT_LT   = "#E8B85C"
SUCCESS     = "#3F9E6B"
DANGER      = "#B23A2E"
PENDING     = "#9AA5B1"

MODULES = ["M1", "M2", "M3", "M4", "M5", "M6"]


# ── INJECTION CSS ────────────────────────────────────────────────────────────
def inject_theme():
    st.markdown(textwrap.dedent(f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"] {{ font-family: 'IBM Plex Sans', sans-serif; }}
    [class^="isc-"], [class*=" isc-"] {{ font-family: 'IBM Plex Sans', sans-serif; }}
    .block-container {{ padding-top: 2.2rem; max-width: 1180px; }}
    h1, h2, h3 {{ font-family: 'IBM Plex Sans', sans-serif; color: {TEXT_900}; letter-spacing: -0.2px; }}
    code, [data-testid="stMetricValue"] {{ font-family: 'IBM Plex Mono', monospace !important; }}
    /* page header (replaces st.title) */
    .isc-eyebrow {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; letter-spacing: 2px; color: {ACCENT}; text-transform: uppercase; margin-bottom: 0.35rem; }}
    .isc-title {{ font-size: 1.65rem; font-weight: 700; color: {TEXT_900}; margin: 0 0 0.7rem 0; }}
    .isc-rule {{ height: 2px; background: linear-gradient(90deg, {ACCENT} 0 48px, {LINE} 48px 100%); margin-bottom: 1.5rem; }}
    /* hero (accueil) */
    .isc-hero {{ background: {INK_900}; padding: 2rem 2.2rem; margin-bottom: 1px; }}
    .isc-hero .isc-eyebrow {{ color: {STEEL_400}; }}
    .isc-hero-title {{ font-size: 1.55rem; font-weight: 700; color: #F4F6F8; letter-spacing: -0.3px; line-height: 1.3; margin-top: 0.4rem; max-width: 640px; }}
    .isc-hero-tag {{ font-size: 0.92rem; color: {STEEL_400}; margin-top: 0.6rem; max-width: 620px; line-height: 1.5; }}
    .isc-dal-badge {{ border: 1px solid {ACCENT}; padding: 0.4rem 0.9rem; text-align: center; flex-shrink: 0; }}
    .isc-dal-badge .lbl {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; color: {ACCENT}; letter-spacing: 1.5px; }}
    .isc-dal-badge .val {{ font-family: 'IBM Plex Mono', monospace; font-size: 1.3rem; font-weight: 700; color: {ACCENT_LT}; }}
    /* rail de pipeline (signature) */
    .isc-rail-wrap {{ margin-top: 1.4rem; padding-top: 1.1rem; border-top: 1px solid {LINE_INK}; }}
    .isc-rail-label {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; letter-spacing: 1.5px; color: {STEEL_600}; margin-bottom: 0.5rem; }}
    .isc-rail {{ display: flex; gap: 4px; }}
    .isc-rail .seg {{ flex: 1; text-align: center; }}
    .isc-rail .bar {{ height: 3px; margin-bottom: 0.4rem; }}
    .isc-rail .lbl {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; }}
    /* rail clair (pour pages internes, hors hero sombre) */
    .isc-rail-wrap.light {{ border-top: 1px solid {LINE}; }}
    .isc-rail-wrap.light .isc-rail-label {{ color: {TEXT_600}; }}
    /* cartes de navigation */
    .isc-card {{ background: {CARD}; border: 1px solid {LINE}; padding: 1.15rem 1.25rem; height: 100%; }}
    .isc-card .num {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; letter-spacing: 1.5px; color: {ACCENT}; margin-bottom: 0.55rem; }}
    .isc-card h4 {{ font-size: 0.95rem; font-weight: 600; color: {TEXT_900}; margin: 0 0 0.35rem 0; }}
    .isc-card p {{ font-size: 0.82rem; color: {TEXT_600}; margin: 0; line-height: 1.5; }}
    /* badges de statut */
    .isc-badge {{ display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; letter-spacing: 0.5px; padding: 0.16rem 0.6rem; border: 1px solid; text-transform: uppercase; }}
    .isc-badge.success {{ color: {SUCCESS}; border-color: {SUCCESS}; }}
    .isc-badge.warning {{ color: {ACCENT}; border-color: {ACCENT}; }}
    .isc-badge.danger  {{ color: {DANGER}; border-color: {DANGER}; }}
    .isc-badge.neutral {{ color: {PENDING}; border-color: {PENDING}; }}
    /* boutons */
    .stButton > button, .stDownloadButton > button {{ border-radius: 2px; font-weight: 600; letter-spacing: 0.2px; }}
    .stButton > button[kind="primary"] {{ background-color: {ACCENT}; border-color: {ACCENT}; color: #1A1204; }}
    .stButton > button[kind="primary"]:hover {{ background-color: {ACCENT_LT}; border-color: {ACCENT_LT}; }}
    hr {{ border-color: {LINE} !important; }}
    [data-testid="stAlert"] {{ border-radius: 2px; font-family: 'IBM Plex Sans', sans-serif; }}
    </style>
    """), unsafe_allow_html=True)


# ── COMPOSANTS ────────────────────────────────────────────────────────────────
def page_header(eyebrow: str, title: str):
    """Remplace st.title(). eyebrow ex. 'MODULE 02 — PIPELINE'."""
    st.markdown(textwrap.dedent(f"""
    <div class="isc-eyebrow">{eyebrow}</div>
    <div class="isc-title">{title}</div>
    <div class="isc-rule"></div>
    """), unsafe_allow_html=True)


def module_rail(done: set, current: str = None, label: str = "PIPELINE M1 \u2192 M6", light: bool = False):
    """Rail segmenté montrant le statut de chaque module.
    done = ensemble des modules déjà générés. current = module en cours (ambre)."""
    segs = ""
    for m in MODULES:
        if m == current:
            color, txt = ACCENT, ACCENT_LT if not light else ACCENT
        elif m in done:
            color, txt = SUCCESS, (STEEL_400 if not light else TEXT_900)
        else:
            color, txt = (LINE_INK if not light else LINE), (STEEL_600 if not light else PENDING)
        segs += f"""<div class="seg">
            <div class="bar" style="background:{color}"></div>
            <div class="lbl" style="color:{txt}">{m}</div>
        </div>"""
    cls = "isc-rail-wrap light" if light else "isc-rail-wrap"
    st.markdown(textwrap.dedent(f"""
    <div class="{cls}">
        <div class="isc-rail-label">{label}</div>
        <div class="isc-rail">{segs}</div>
    </div>
    """), unsafe_allow_html=True)


def badge(text: str, kind: str = "neutral") -> str:
    """Retourne un badge HTML inline. kind: success / warning / danger / neutral."""
    return f'<span class="isc-badge {kind}">{text}</span>'


def nav_card(num: str, title: str, desc: str):
    st.markdown(textwrap.dedent(f"""
    <div class="isc-card">
        <div class="num">{num}</div>
        <h4>{title}</h4>
        <p>{desc}</p>
    </div>
    """), unsafe_allow_html=True)
