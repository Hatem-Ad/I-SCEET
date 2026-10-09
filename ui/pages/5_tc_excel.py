"""
================================================================================
 I-SCEET — Page 5 : TC Excel (Technical Comments)
 File: ui/pages/5_tc_excel.py
 Copyright (c) 2026 Hatem Adouani — MIT License
================================================================================
 v3: added reviewer acronym field per remark, a delete button per remark,
 and switched the AI-resolution button from "one remark = one click" to
 "one click per module" - since pc_pipeline.py's _get_tc_remarks() already
 bundles ALL open remarks for a module into a single generation request,
 sending them one at a time was both slower and misleading (each
 individual send actually re-sent every other open remark for that module
 too, just re-triggering the same regeneration repeatedly).
================================================================================
"""

import streamlit as st
import sys, os
import pandas as pd
from io import BytesIO
from collections import defaultdict

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Backend.db import (
    get_artifacts,
    save_tc_remark,
    get_tc_remarks,
    update_tc_status,
    delete_tc_remark,
    get_project_runtime_value,
)
from orchestrator.pc_pipeline import PCPipeline
from theme import inject_theme, page_header, badge

st.set_page_config(page_title="TC Excel — I-SCEET", layout="wide")
inject_theme()
page_header("WORKSPACE 05 • CORRECTIVE ACTION", "Remarques techniques & boucle de correction", "Capture review remarks, export or import TC logs and relaunch the relevant generation modules with correction context.")
st.caption("Documentez vos remarques techniques. Toutes les remarques 'open' d'un module sont envoyées ensemble, en un clic, pour résolution automatique.")

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
        Aucun projet actif.
    </div>
    """,
    unsafe_allow_html=True,
)
    st.stop()

st.markdown(f"**Projet actif :** {active['name']} — DAL {active['dal_level']}")
st.divider()

artifacts = get_artifacts(active["id"])
available_modules = sorted({a["module"] for a in artifacts
                            if a["module"] in ["M1","M2","M3","M4","M5","M6"]})
colab_url = (
    st.session_state.get(f"colab_url_project_{active['id']}")
    or get_project_runtime_value(active["id"], "colab_url", "")
    or st.session_state.get("colab_url", "")
)
if colab_url:
    st.session_state[f"colab_url_project_{active['id']}"] = colab_url
    st.session_state["colab_url"] = colab_url

tab1, tab2, tab3 = st.tabs(["Ajouter une remarque", "Liste des remarques", "Export / Import Excel"])

# ── TAB 1 : ADD REMARK ────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Nouvelle remarque technique")
    col1, col2 = st.columns(2)
    with col1:
        module = st.selectbox("Module concerné", available_modules or ["M1","M2","M3","M4","M5","M6"])
        document = st.text_input("Document", placeholder="ex: SRD, SDDD, boot.c")
    with col2:
        req_id = st.text_input("ID Exigence", placeholder="ex: HLR-CLK-002, LLR-CLK-002-01")
        reviewer = st.text_input("Reviewer (acronyme)", placeholder="ex: HAT", max_chars=10)

    remark = st.text_area("Remarque technique", height=100,
                           placeholder="Ex: Diviser HLR-CLK-002 en deux exigences séparées\n"
                                       "Ex: Timing insuffisant, mettre 200ms au lieu de 500ms")

    if st.button("Ajouter la remarque", type="primary", disabled=not remark):
        save_tc_remark(active["id"], module, document, req_id, remark, reviewer=reviewer)
        st.success("Remarque ajoutée.")
        st.rerun()

# ── TAB 2 : LIST (grouped by module) ─────────────────────────────────────────
with tab2:
    st.markdown("### Remarques enregistrées")
    remarks = get_tc_remarks(active["id"])

    if not remarks:
        st.info("Aucune remarque. Ajoutez-en via l'onglet **Ajouter**.")
    else:
        status_kind = {"open": "danger", "closed": "success",
                       "in_progress": "warning", "rejected": "neutral"}
        status_text = {"open": "Ouverte", "closed": "Fermée",
                       "in_progress": "En cours (à revoir)", "rejected": "Rejetée"}

        by_module = defaultdict(list)
        for r in remarks:
            by_module[r["module"]].append(r)

        for module_name, module_remarks in by_module.items():
            open_count = sum(1 for r in module_remarks if r["status"] == "open")

            hcol1, hcol2 = st.columns([3, 1])
            with hcol1:
                st.markdown(f"#### {module_name} ({len(module_remarks)} remarque(s), {open_count} ouverte(s))")
            with hcol2:
                if open_count > 0:
                    if st.button(
                        f"Envoyer les {open_count} remarque(s) ouverte(s)",
                        key=f"send_all_{module_name}", disabled=not colab_url,
                        help="Relance le module UNE fois, avec toutes ses remarques ouvertes en contexte" if colab_url
                             else "Connecte Colab sur 2 Pipeline d'abord"
                    ):
                        st.session_state[f"resolving_module_{module_name}"] = True
                        st.rerun()

            if st.session_state.get(f"resolving_module_{module_name}"):
                status_area = st.empty()
                status_area.markdown(f"Envoi des remarques à **{module_name}**...")

                pipeline = PCPipeline(colab_url, active["id"], active["name"])

                def cb(mod, message):
                    status_area.markdown(message)

                result = pipeline.run_single(module_name, progress_callback=cb)
                st.session_state[f"resolving_module_{module_name}"] = False

                if result.get("status") == "success":
                    response = (
                        f"Régénéré {module_name} avec les {open_count} remarque(s) ouverte(s) "
                        f"en contexte → v{result.get('version', '?')}. À revoir dans 3 Revue "
                        f"avant de confirmer closed/rejected."
                    )
                    for r in module_remarks:
                        if r["status"] == "open":
                            update_tc_status(r["id"], "in_progress", response)
                    status_area.success(response)
                else:
                    response = f"Échec de la régénération : {result.get('message', 'erreur inconnue')}"
                    status_area.error(response)
                st.rerun()

            for r in module_remarks:
                col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 3, 1.4, 1.4, 0.5])
                with col1:
                    st.caption(r["document"])
                with col2:
                    st.caption(r["req_id"] or "—")
                with col3:
                    st.markdown(r["remark"])
                    if r.get("model_response"):
                        st.info(r['model_response'])
                    st.caption(f"Reviewer: {r.get('reviewer') or '—'}")
                with col4:
                    status_options = ["open", "in_progress", "closed", "rejected"]
                    new_status = st.selectbox(
                        "Statut", status_options,
                        index=status_options.index(r["status"]) if r["status"] in status_options else 0,
                        key=f"tc_status_{r['id']}", label_visibility="collapsed"
                    )
                    if new_status != r["status"]:
                        update_tc_status(r["id"], new_status, r.get("model_response", ""))
                        st.rerun()
                with col5:
                    kind = status_kind.get(r["status"], "neutral")
                    label = status_text.get(r["status"], r["status"])
                    st.markdown(badge(label, kind), unsafe_allow_html=True)
                with col6:
                    if st.button("Suppr.", key=f"del_{r['id']}", help="Supprimer cette remarque"):
                        st.session_state[f"confirm_del_{r['id']}"] = True
                        st.rerun()

                if st.session_state.get(f"confirm_del_{r['id']}"):
                    st.warning(f"Supprimer définitivement cette remarque ?")
                    cc1, cc2 = st.columns([1, 4])
                    with cc1:
                        if st.button("Confirmer", key=f"confirm_del_yes_{r['id']}"):
                            delete_tc_remark(r["id"])
                            st.session_state[f"confirm_del_{r['id']}"] = False
                            st.rerun()
                    with cc2:
                        if st.button("Annuler", key=f"confirm_del_no_{r['id']}"):
                            st.session_state[f"confirm_del_{r['id']}"] = False
                            st.rerun()

            st.divider()

# ── TAB 3 : EXPORT / IMPORT ──────────────────────────────────────────────────
with tab3:
    st.markdown("### Export Excel")
    remarks = get_tc_remarks(active["id"])

    if remarks:
        df = pd.DataFrame(remarks)[["module","document","req_id","remark","reviewer","status","model_response","created_at"]]
        df.columns = ["Module","Document","ID Req","Remarque","Reviewer","Statut","Réponse modèle","Date"]

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="TC_Remarks")
        buffer.seek(0)

        st.download_button(
            label="Télécharger TC.xlsx",
            data=buffer,
            file_name=f"TC_{active['name']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        st.dataframe(df, width="stretch")
    else:
        st.info("Aucune remarque à exporter.")

    st.divider()
    st.markdown("### Import Excel (remarques corrigées)")
    uploaded_tc = st.file_uploader("Uploader TC.xlsx mis à jour", type=["xlsx"])
    if uploaded_tc:
        df_import = pd.read_excel(uploaded_tc)
        st.dataframe(df_import, width="stretch")
        if st.button("Importer les remarques", type="primary"):
            count = 0
            for _, row in df_import.iterrows():
                if pd.notna(row.get("Remarque")) and str(row.get("Remarque")).strip():
                    save_tc_remark(
                        active["id"],
                        str(row.get("Module", "")),
                        str(row.get("Document", "")),
                        str(row.get("ID Req", "")),
                        str(row.get("Remarque", "")),
                        reviewer=str(row.get("Reviewer", "") or "")
                    )
                    count += 1
            st.success(f"{count} remarques importées.")
            st.rerun()