"""
================================================================================
 I-SCEET — Page 1 : Upload documents + Nouveau projet
 File: ui/pages/1_upload.py
================================================================================
 v2: each file is saved immediately on upload (no all-or-nothing batch
 button) so a project can be built up incrementally - upload just the HW
 doc today, add the rest later, each new upload becomes the new version
 used by the next generation. Real text is extracted from docx/pdf/txt
 instead of a "[FILE: name]" placeholder.
================================================================================
"""

import streamlit as st
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from Backend.db import create_project, get_all_projects, save_artifact, get_artifact_by_module

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="Upload — I-SCEET", page_icon="📤", layout="wide")
st.title("📤 Nouveau projet — Upload documents")
st.divider()


# ── TEXT EXTRACTION ────────────────────────────────────────────────────────────
def extract_text(file) -> str:
    """Extract real text content from an uploaded docx/pdf/txt file.
    Never returns a placeholder - callers should treat an empty result
    as extraction failure, not as 'no content'."""
    name = file.name.lower()
    file.seek(0)
    try:
        if name.endswith(".docx"):
            import docx
            d = docx.Document(file)
            parts = [p.text for p in d.paragraphs if p.text.strip()]
            for t in d.tables:
                for row in t.rows:
                    parts.append(" | ".join(c.text for c in row.cells))
            return "\n".join(parts)
        elif name.endswith(".pdf"):
            import pdfplumber
            parts = []
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        parts.append(text)
            return "\n".join(parts)
        elif name.endswith(".txt"):
            return file.read().decode("utf-8", errors="replace")
    except Exception as e:
        st.error(f"⚠️ Extraction failed for {file.name}: {e}")
        return ""
    return ""


# ── STEP 1 : PROJECT ──────────────────────────────────────────────────────────
st.markdown("### Étape 1 — Créer le projet")
col1, col2 = st.columns([2, 1])
with col1:
    project_name = st.text_input("Nom du projet", placeholder="ex: STM32F303_Bootloader_v1")
with col2:
    dal_level = st.selectbox("Niveau DAL", ["A", "B", "C", "D"])

if st.button("➕ Créer le projet", type="primary", disabled=not project_name):
    existing = [p["name"] for p in get_all_projects()]
    if project_name in existing:
        st.error(f"Un projet nommé **{project_name}** existe déjà.")
    else:
        pid = create_project(project_name, dal_level)
        st.session_state["active_project"] = {"id": pid, "name": project_name, "dal_level": dal_level}
        st.success(f"✅ Projet **{project_name}** créé (ID: {pid})")

st.divider()

active = st.session_state.get("active_project")
if not active:
    st.warning("⚠️ Créez ou sélectionnez un projet ci-dessus avant d'uploader des documents.")
    st.stop()


# ── SHARED: one uploader that saves immediately ────────────────────────────────
def extract_version_from_docx(file):
    """Try to read the Version/Status from a docx cover-page table (the
    'Document ID'/'Version'/'Status' pattern used by every doc this
    project generates). Returns a version dict, or None if the file
    isn't a docx or doesn't have a parseable cover table - callers
    should fall back to normal auto-versioning (starts at 1.0) in that
    case, not assume 1.0 outright."""
    if not file.name.lower().endswith(".docx"):
        return None
    try:
        import docx
        file.seek(0)
        d = docx.Document(file)
        if not d.tables:
            return None
        fields = {row.cells[0].text.strip(): row.cells[1].text.strip()
                  for row in d.tables[0].rows if len(row.cells) >= 2}
        version_str = fields.get("Version", "").strip()
        status_str = fields.get("Status", "DRAFT").strip().upper()
        if not version_str:
            return None
        if "." in version_str:
            baseline_str, minor_str = version_str.split(".", 1)
        else:
            baseline_str, minor_str = version_str, "0"
        return {
            "baseline_number": int(baseline_str),
            "minor_number": int(minor_str),
            "status": "BASELINE" if "BASELINE" in status_str else "DRAFT",
        }
    except Exception:
        return None


def doc_uploader(doc_id, doc_label, module, col):
    """Render one uploader. Saves to DB immediately when a file is given -
    no batch step. Shows the currently-saved version, if any, so partial/
    incremental uploads are visible."""
    with col:
        current = get_artifact_by_module(active["id"], doc_id)
        status = f"✅ v{current['version']} saved ({current['created_at'][:16]})" if current else "⬜ not uploaded yet"
        st.markdown(f"**{doc_id}** — {doc_label}")
        st.caption(status)
        f = st.file_uploader(
            "Upload", type=["docx", "pdf", "txt"], key=f"up_{doc_id}",
            label_visibility="collapsed"
        )
        if f is not None:
            text = extract_text(f)
            if not text.strip():
                st.error(f"❌ Could not extract text from {f.name} — not saved. Try re-exporting the file.")
                return
            path = os.path.join(UPLOAD_DIR, f"{active['id']}_{doc_id}_{f.name}")
            f.seek(0)
            with open(path, "wb") as out:
                out.write(f.read())
            detected_version = extract_version_from_docx(f)
            save_artifact(active["id"], module, doc_id, text, path, version=detected_version)
            if detected_version:
                v = detected_version
                st.success(
                    f"✅ {doc_id} saved as v{v['baseline_number']}.{v['minor_number']} "
                    f"({v['status']}) — version detected from the document's own cover "
                    f"page, not reset to 1.0."
                )
            else:
                st.success(f"✅ {doc_id} saved ({len(text):,} chars extracted) — no version "
                           f"detected in the file, started at v1.0.")
            st.rerun()


# ── STEP 2 : PLANNING & STANDARDS ────────────────────────────────────────────
planning_docs = {
    "PSAC": "Plan for Software Aspects of Certification",
    "SDP":  "Software Development Plan",
    "SVP":  "Software Verification Plan",
    "SCMP": "Software Configuration Management Plan",
    "SQAP": "Software Quality Assurance Plan",
    "SRS":  "Software Requirements Standards",
    "SDS":  "Software Design Standards",
    "SCS":  "Software Code Standards",
    "SVS":  "Software Verification Standard",
}

st.markdown(f"### Étape 2 — Documents DO-178C ({len(planning_docs)} documents)")
st.caption(
    "Plans et standards — injectés dans chaque module. Chaque document est "
    "sauvegardé dès l'upload — pas besoin des les avoir tous en même temps. "
    "Un nouvel upload remplace la version utilisée par la prochaine génération."
)

cols = st.columns(2)
for i, (doc_id, doc_name) in enumerate(planning_docs.items()):
    doc_uploader(doc_id, doc_name, "PLANNING", cols[i % 2])

st.divider()

# ── STEP 3 : M1 INPUTS ────────────────────────────────────────────────────────
st.markdown("### Étape 3 — Inputs M1 (3 documents)")
st.caption(
    "Documents source pour la génération des HLR. Chacun peut être "
    "uploadé indépendamment — par exemple juste le Hardware doc seul."
)

col1, col2, col3 = st.columns(3)
doc_uploader("PDS", "📄 Product Design Specification", "M1_INPUT", col1)
doc_uploader("ARCH", "🏗️ Architecture Système", "M1_INPUT", col2)
doc_uploader("HW", "🔧 Hardware Documentation", "M1_INPUT", col3)

st.divider()

# ── SUMMARY ───────────────────────────────────────────────────────────────────
all_doc_ids = list(planning_docs.keys()) + ["PDS", "ARCH", "HW"]
saved = [d for d in all_doc_ids if get_artifact_by_module(active["id"], d)]
st.markdown(f"### 📊 {len(saved)}/{len(all_doc_ids)} documents sauvegardés")
if len(saved) < len(all_doc_ids):
    missing = [d for d in all_doc_ids if d not in saved]
    st.info(f"Documents manquants : {', '.join(missing)}. Le pipeline peut déjà tourner avec ce qui est présent — les modules utiliseront ce qui est disponible en base.")
else:
    st.success("Tous les documents sont présents.")
    st.page_link("pages/2_pipeline.py", label="Aller au Pipeline", icon="⚙️")