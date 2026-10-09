"""
================================================================================
 I-SCEET — Page 3 : Revue globale
 File: ui/pages/3_revue.py
 Copyright (c) 2026 Hatem Adouani — MIT License
================================================================================
 v2: fixed a real bug - the old dict comprehension {a["module"]: a for a in
 artifacts} silently kept only the LAST artifact per module, so once M2
 started producing 3 artifacts (SDDD, DD, CT) only one of them ever showed
 up. Now groups by module -> list of artifacts, and DD/CT (xlsx, content="")
 get a spreadsheet preview read from file_path instead of an empty text box.
 Names updated: SVCP-LLT-001/SVCP-HLT-001 -> SUTC, STD-001 -> TM.
================================================================================
"""

import streamlit as st
import sys, os
import difflib

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Backend.db import (get_artifacts, save_review, get_reviews,
                        get_artifact_history, baseline_artifact)
from theme import inject_theme, page_header, PAPER

st.set_page_config(page_title="Revue — I-SCEET", layout="wide")
inject_theme()
page_header("WORKSPACE 03 • ASSURANCE", "Revue des artefacts & gestion des baselines", "Review generated outputs, compare versions, record decisions and freeze baseline references.")

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
        margin-bottom: 1rem;
    ">
        Aucun projet actif. Rendez-vous sur
        <strong>1 Upload</strong> d'abord.
    </div>
    """,
    unsafe_allow_html=True,
)
    st.stop()

st.markdown(f"**Projet :** {active['name']} \u2014 DAL {active['dal_level']}")
st.divider()

artifacts = get_artifacts(active["id"])

# Group by module -> {type: artifact}, keeping the latest version of each type
by_module = {}
for a in artifacts:
    if a["module"] not in ["M1", "M2", "M3", "M4", "M5", "M6"]:
        continue
    by_module.setdefault(a["module"], {})
    existing = by_module[a["module"]].get(a["type"])
    if existing is None or a.get("version", 0) >= existing.get("version", 0):
        by_module[a["module"]][a["type"]] = a

if not by_module:
    st.info("Aucun artefact pour l'instant. Lancez le pipeline sur **2 Pipeline** d'abord.")
    st.stop()

existing_reviews = {r["module"]: r for r in get_reviews(active["id"])}

MODULE_INFO = {
    "M1": ("High Level Requirements",              ["SRD"]),
    "M2": ("Low Level Requirements + Architecture", ["SDDD", "DD", "CT"]),
    "M3": ("Source Code C",                         ["/src"]),
    "M4": ("Low Level Tests",                       ["SUTC"]),
    "M5": ("High Level Tests",                      ["SVTC"]),
    "M6": ("Traceability Matrix",                   ["TM"]),
}

# ── SUMMARY BAR ───────────────────────────────────────────────────────────────
reviews = get_reviews(active["id"])
c1, c2, c3, c4 = st.columns(4)
c1.metric("Modules générés", f"{len(by_module)}/6")
c2.metric("Approuvés",  sum(1 for r in reviews if r["status"] == "approved"))
c3.metric("À réviser",  sum(1 for r in reviews if r["status"] == "needs_revision"))
c4.metric("Rejetés",  sum(1 for r in reviews if r["status"] == "rejected"))

st.divider()


def render_baseline_section(artifact, project_id, module_id):
    """Bouton Baseline, avec un diff façon Beyond-Compare vs la version
    précédente affiché avant confirmation - une baseline n'est jamais
    verrouillée à l'aveugle."""
    st.divider()
    st.markdown('<span class="isc-eyebrow">Baseline de cet artefact</span>', unsafe_allow_html=True)

    if artifact["status"] == "BASELINE":
        st.info(
            f"Ceci est déjà une BASELINE (v{artifact['version']}, "
            f"baselinée le {artifact.get('baselined_at', '')[:16]} par "
            f"{artifact.get('baselined_by', '—')}). "
            f"Générez un nouveau brouillon pour continuer."
        )
        return

    st.caption(f"Brouillon actuel : v{artifact['version']} (DRAFT)")

    confirm_key = f"confirm_baseline_{artifact['id']}"
    show_key = f"show_diff_{artifact['id']}"

    if not st.session_state.get(show_key):
        if st.button("Baseliner cette version", key=f"start_baseline_{artifact['id']}"):
            st.session_state[show_key] = True
            st.rerun()
        return

    # ── DIFF VIEW ────────────────────────────────────────────────────────────
    history = get_artifact_history(project_id, module_id, artifact["type"])
    previous = None
    for h in reversed(history):
        if h["id"] != artifact["id"]:
            previous = h
            break

    if previous and artifact.get("content") and previous.get("content"):
        st.markdown(f"**Diff vs version précédente (v{previous['version']}, {previous['status']}) :**")
        differ = difflib.HtmlDiff(wrapcolumn=80)
        html = differ.make_table(
            previous["content"].splitlines(),
            artifact["content"].splitlines(),
            fromdesc=f"v{previous['version']}",
            todesc=f"v{artifact['version']} (à baseliner)",
            context=True, numlines=3
        )
        # HtmlDiff produces a bare table - wrap with palette-aligned styling
        styled = f"""
        <style>
          table.diff {{font-family: 'IBM Plex Mono', monospace; font-size: 12px; width: 100%; border-collapse: collapse;}}
          td.diff_header {{background: {PAPER};}}
          .diff_add {{background-color: #E3F3EA;}}
          .diff_chg {{background-color: #FBF0DC;}}
          .diff_sub {{background-color: #F7E4E1;}}
        </style>
        {html}
        """
        st.components.v1.html(styled, height=400, scrolling=True)
    elif not previous:
        st.info("Aucune version précédente à comparer — ce serait la première baseline.")
    else:
        st.warning("Diff indisponible pour ce type d'artefact (pas de contenu texte, ex. classeurs DD/CT) — vérifiez le fichier directement avant de confirmer.")

    # ── CONFIRMATION ─────────────────────────────────────────────────────────
    description = st.text_area(
        "Description du changement (requis — alimente l'historique de révision et le registre SCI du SCMP)",
        placeholder="ex: Approuvé pour SOI #1 — carte mémoire corrigée, alignée avec ARCH",
        key=f"desc_{artifact['id']}"
    )
    baselined_by = st.text_input("Baseliné par", key=f"by_{artifact['id']}")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Confirmer la baseline", type="primary",
                     disabled=not description.strip(), key=f"confirm_{artifact['id']}"):
            new_id = baseline_artifact(artifact["id"], description, baselined_by or "unknown")
            st.session_state[show_key] = False
            st.success(f"Baseliné — nouvel id d'artefact {new_id}")
            st.rerun()
    with col2:
        if st.button("Annuler", key=f"cancel_{artifact['id']}"):
            st.session_state[show_key] = False
            st.rerun()


def render_text_artifact(artifact, module_id):
    content = artifact.get("content", "")
    if module_id == "M3":
        st.code(content[:5000], language="c")
        if len(content) > 5000:
            st.caption(f"... affichage des 5000 premiers caractères sur {len(content):,}")
    else:
        st.text_area("Contenu complet", value=content, height=350,
                     key=f"content_{artifact['type']}_{artifact['id']}", disabled=True)
    st.download_button(
        label=f"Télécharger {artifact['type']}",
        data=content, file_name=f"{artifact['type']}_{active['name']}.txt",
        mime="text/plain", key=f"dl_{artifact['type']}_{artifact['id']}"
    )


def render_xlsx_artifact(artifact):
    path = artifact.get("file_path", "")
    if not path or not os.path.exists(path):
        st.warning(f"Fichier introuvable sur le disque : {path or '(aucun chemin enregistré)'}")
        return
    try:
        import pandas as pd
        xls = pd.ExcelFile(path)
        tabs = st.tabs(xls.sheet_names)
        for tab, sheet in zip(tabs, xls.sheet_names):
            with tab:
                df = xls.parse(sheet)
                st.dataframe(df, width="stretch", height=300)
    except Exception as e:
        st.error(f"Aperçu du classeur impossible : {e}")
    with open(path, "rb") as f:
        st.download_button(
            label=f"Télécharger {artifact['type']}.xlsx",
            data=f.read(), file_name=os.path.basename(path),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{artifact['type']}_{artifact['id']}"
        )


# ── ARTIFACT VIEWER ───────────────────────────────────────────────────────────
for module_id in ["M1", "M2", "M3", "M4", "M5", "M6"]:
    if module_id not in by_module:
        continue

    module_desc, expected_types = MODULE_INFO[module_id]
    module_files = by_module[module_id]
    prev_review = existing_reviews.get(module_id)

    status_code = ("OK" if prev_review and prev_review["status"] == "approved"
                   else "REV" if prev_review and prev_review["status"] == "needs_revision"
                   else "REJ" if prev_review and prev_review["status"] == "rejected"
                   else "--")

    present_types = [t for t in expected_types if t in module_files]
    types_label = " + ".join(present_types) if present_types else "aucune sortie"

    with st.expander(
        f"[{status_code}]  {module_id} \u2014 {types_label} \u2014 {module_desc}",
        expanded=(module_id == "M1")
    ):
        tab_labels = [t for t in present_types] + ["Revue"]
        tabs = st.tabs(tab_labels)

        for tab, artifact_type in zip(tabs, present_types):
            with tab:
                artifact = module_files[artifact_type]
                st.caption(
                    f"Généré : {artifact.get('created_at', '')[:16]} | "
                    f"Version : {artifact.get('version', 1)}"
                )
                if artifact_type in ("DD", "CT"):
                    render_xlsx_artifact(artifact)
                else:
                    render_text_artifact(artifact, module_id)
                render_baseline_section(artifact, active["id"], module_id)

        # ── REVIEW TAB (last tab) ───────────────────────────────────────────
        with tabs[-1]:
            st.markdown("**Décision de revue :**")

            status_options = ["approved", "needs_revision", "rejected"]
            status_labels = {
                "approved": "Approuvé",
                "needs_revision": "À réviser",
                "rejected": "Rejeté"
            }
            current_status = prev_review["status"] if prev_review else "needs_revision"

            col1, col2 = st.columns([1, 2])
            with col1:
                status = st.radio(
                    "Statut", status_options,
                    format_func=lambda x: status_labels[x],
                    index=status_options.index(current_status),
                    key=f"status_{module_id}"
                )
            with col2:
                notes = st.text_area(
                    "Notes de revue",
                    value=prev_review["notes"] if prev_review else "",
                    placeholder="ex: HLR-006 timing incorrect, à scinder en 2...\n"
                                "ex: LLR-CLK-002-01 gestion du timeout manquante...",
                    height=120, key=f"notes_{module_id}"
                )
                reviewer = st.text_input(
                    "Nom du relecteur",
                    value=prev_review.get("reviewer", "") if prev_review else "",
                    key=f"reviewer_{module_id}"
                )

            if st.button(f"Enregistrer la revue {module_id}", key=f"save_{module_id}", type="primary"):
                save_review(active["id"], module_id, "+".join(present_types), status, notes, reviewer)
                st.success(f"Revue enregistrée \u2014 {status_labels[status]}")
                if status in ["needs_revision", "rejected"]:
                    st.info("Rendez-vous sur **5 TC Excel** pour documenter vos remarques techniques en vue d'une régénération.")
                st.rerun()

st.divider()

# ── GLOBAL ACTIONS ────────────────────────────────────────────────────────────
reviews = get_reviews(active["id"])
approved_count = sum(1 for r in reviews if r["status"] == "approved")

if approved_count == len(by_module) == 6:
    st.success("Les 6 modules sont approuvés. Projet complet.")
elif len(reviews) > 0:
    needs_fix = sum(1 for r in reviews if r["status"] in ["needs_revision", "rejected"])
    if needs_fix > 0:
        st.warning(
            f"{needs_fix} artefact(s) à réviser. "
            "Rendez-vous sur **5 TC Excel** pour ajouter des remarques techniques, "
            "puis relancez le module sur **2 Pipeline**."
        )