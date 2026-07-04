"""
================================================================================
 I-SCEET — Page 5 : TC Excel (Technical Comments)
 File: ui/pages/5_tc_excel.py
================================================================================
 v2: was 100% manual — status dropdown only, model_response column existed
 in the DB but nothing ever filled it. Adds a "🤖 Envoyer au modèle"
 button per open remark: re-runs the remark's module (pc_pipeline.py
 already injects open remarks as tc_remarks into the generation request —
 this was already wired, just never triggered from here), fills
 model_response with what happened, and moves the remark to
 in_progress so a human confirms closed/rejected after reviewing the
 new artifact in 3 Revue — the AI never self-closes a remark.
================================================================================
"""

import streamlit as st
import sys, os
import pandas as pd
from io import BytesIO

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from Backend.db import (get_artifacts, save_tc_remark,
                         get_tc_remarks, update_tc_status)
from orchestrator.pc_pipeline import PCPipeline

st.set_page_config(page_title="TC Excel — I-SCEET", page_icon="📊", layout="wide")
st.title("📊 Technical Comments (TC Excel)")
st.caption("Documentez vos remarques techniques. Une remarque 'open' peut être envoyée au modèle concerné pour résolution automatique.")
st.divider()

active = st.session_state.get("active_project")
if not active:
    st.warning("⚠️ Aucun projet actif.")
    st.stop()

artifacts = get_artifacts(active["id"])
available_modules = sorted({a["module"] for a in artifacts
                            if a["module"] in ["M1","M2","M3","M4","M5","M6"]})
colab_url = st.session_state.get("colab_url", "")

tab1, tab2, tab3 = st.tabs(["➕ Ajouter une remarque", "📋 Liste des remarques", "📥 Export / Import Excel"])

# ── TAB 1 : ADD REMARK ────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Nouvelle remarque technique")
    col1, col2 = st.columns(2)
    with col1:
        module = st.selectbox("Module concerné", available_modules or ["M1","M2","M3","M4","M5","M6"])
        document = st.text_input("Document", placeholder="ex: SRD, SDDD, boot.c")
    with col2:
        req_id = st.text_input("ID Exigence", placeholder="ex: HLR-CLK-002, LLR-CLK-002-01")

    remark = st.text_area("Remarque technique", height=100,
                           placeholder="Ex: Diviser HLR-CLK-002 en deux exigences séparées\n"
                                       "Ex: Timing insuffisant, mettre 200ms au lieu de 500ms")

    if st.button("➕ Ajouter la remarque", type="primary", disabled=not remark):
        save_tc_remark(active["id"], module, document, req_id, remark)
        st.success("✅ Remarque ajoutée !")
        st.rerun()

# ── TAB 2 : LIST ──────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### Remarques enregistrées")
    remarks = get_tc_remarks(active["id"])

    if not remarks:
        st.info("Aucune remarque. Ajoutez-en via l'onglet **Ajouter**.")
    else:
        status_labels = {"open": "🔴 Open", "closed": "🟢 Closed",
                         "in_progress": "🟡 In progress (à revoir)", "rejected": "⚫ Rejected"}

        for r in remarks:
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 3, 2])
            with col1:
                st.markdown(f"**{r['module']}**")
            with col2:
                st.caption(r["document"])
            with col3:
                st.caption(r["req_id"] or "—")
            with col4:
                st.markdown(r["remark"])
                if r.get("model_response"):
                    st.info(f"🤖 {r['model_response']}")
            with col5:
                status_options = ["open", "in_progress", "closed", "rejected"]
                new_status = st.selectbox(
                    "Statut", status_options,
                    index=status_options.index(r["status"]) if r["status"] in status_options else 0,
                    key=f"tc_status_{r['id']}", label_visibility="collapsed"
                )
                if new_status != r["status"]:
                    update_tc_status(r["id"], new_status, r.get("model_response", ""))
                    st.rerun()

                if r["status"] == "open":
                    if st.button("🤖 Envoyer au modèle", key=f"send_{r['id']}",
                                disabled=not colab_url,
                                help="Relance le module concerné avec cette remarque en contexte" if colab_url
                                     else "Connecte Colab sur 2 Pipeline d'abord"):
                        st.session_state[f"resolving_{r['id']}"] = True
                        st.rerun()

            if st.session_state.get(f"resolving_{r['id']}"):
                status_area = st.empty()
                status_area.markdown(f"⏳ Envoi de la remarque à **{r['module']}**...")

                pipeline = PCPipeline(colab_url, active["id"], active["name"])

                def cb(module, message):
                    status_area.markdown(message)

                result = pipeline.run_single(r["module"], progress_callback=cb)
                st.session_state[f"resolving_{r['id']}"] = False

                if result.get("status") == "success":
                    response = (
                        f"Régénéré {r['module']} avec cette remarque en contexte "
                        f"→ v{result.get('version', '?')}. À revoir dans 3 Revue avant "
                        f"de confirmer closed/rejected."
                    )
                    update_tc_status(r["id"], "in_progress", response)
                    status_area.success(f"✅ {response}")
                else:
                    response = f"Échec de la régénération : {result.get('message', 'erreur inconnue')}"
                    update_tc_status(r["id"], "open", response)
                    status_area.error(f"❌ {response}")
                st.rerun()

            st.divider()

# ── TAB 3 : EXPORT / IMPORT ──────────────────────────────────────────────────
with tab3:
    st.markdown("### Export Excel")
    remarks = get_tc_remarks(active["id"])

    if remarks:
        df = pd.DataFrame(remarks)[["module","document","req_id","remark","status","model_response","created_at"]]
        df.columns = ["Module","Document","ID Req","Remarque","Statut","Réponse modèle","Date"]

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="TC_Remarks")
        buffer.seek(0)

        st.download_button(
            label="⬇️ Télécharger TC.xlsx",
            data=buffer,
            file_name=f"TC_{active['name']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucune remarque à exporter.")

    st.divider()
    st.markdown("### Import Excel (remarques corrigées)")
    uploaded_tc = st.file_uploader("Uploader TC.xlsx mis à jour", type=["xlsx"])
    if uploaded_tc:
        df_import = pd.read_excel(uploaded_tc)
        st.dataframe(df_import, use_container_width=True)
        if st.button("📥 Importer les remarques", type="primary"):
            count = 0
            for _, row in df_import.iterrows():
                if pd.notna(row.get("Remarque")) and str(row.get("Remarque")).strip():
                    save_tc_remark(
                        active["id"],
                        str(row.get("Module", "")),
                        str(row.get("Document", "")),
                        str(row.get("ID Req", "")),
                        str(row.get("Remarque", ""))
                    )
                    count += 1
            st.success(f"✅ {count} remarques importées !")
            st.rerun()