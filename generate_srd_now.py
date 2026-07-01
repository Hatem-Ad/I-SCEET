"""
================================================================================
 I-SCEET — Génération immédiate du SRD.docx depuis la DB existante
 File: generate_srd_now.py (à placer à la racine du repo)
================================================================================
 Usage:
   python3 generate_srd_now.py

 Ce script :
 1. Se connecte à isceet.db
 2. Récupère le dernier output texte de M1 pour le projet actif
 3. Le convertit en SRD-0xx.docx via docx_builder
 4. Sauvegarde dans outputs/<projet>/SRD-0xx.docx
================================================================================
"""

import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(__file__))

from orchestrator.docx_builder import build_srd

DB_PATH = os.path.join(os.path.dirname(__file__), "isceet.db")


def get_latest_m1_output():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get most recently updated project
    c.execute("SELECT id, name FROM projects ORDER BY updated_at DESC LIMIT 1")
    project = c.fetchone()
    if not project:
        print("❌ Aucun projet trouvé dans la DB.")
        return None, None, None

    # Get latest M1 artifact for this project
    c.execute(
        """SELECT content, version FROM artifacts
           WHERE project_id=? AND module='M1'
           ORDER BY created_at DESC LIMIT 1""",
        (project["id"],)
    )
    artifact = c.fetchone()
    conn.close()

    if not artifact:
        print(f"❌ Aucun output M1 trouvé pour le projet '{project['name']}'.")
        return None, None, None

    return artifact["content"], artifact["version"] or "1.0", project["name"]


def main():
    print("🔍 Recherche du dernier output M1 dans isceet.db...")
    text, version, project_name = get_latest_m1_output()

    if not text:
        sys.exit(1)

    print(f"✅ Trouvé : projet '{project_name}', version {version}, {len(text)} caractères")

    out_dir = os.path.join(os.path.dirname(__file__), "outputs", project_name)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"SRD-0xx_v{version}.docx")

    print(f"📄 Génération du document Word...")
    path = build_srd(text, out_path, version=str(version), project=project_name)

    print(f"\n✅ TERMINÉ : {path}")
    print(f"   Taille : {os.path.getsize(path) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
