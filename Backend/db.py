import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "isceet.db")

# ── DOCUMENT NAMING CONVENTIONS ────────────────────────────────────────────────
# Every artifact is identified by (family name, baseline_number, minor_number,
# status). The formatted Document ID / Version string is always COMPUTED from
# these, never stored pre-formatted - this is what the whole "grand ménage"
# session was about: stop having the displayed ID and the Version field able
# to drift out of sync.
#
#   PLANNING_FAMILIES : bare name never changes (e.g. "PSAC"); Version field
#       is always "{baseline}.{minor}"; Status (DRAFT/BASELINE) is the only
#       thing that differs between a draft and a baselined revision.
#   Everything else (standards, and AI-pipeline outputs SRD/SDDD/DD/CT/SUTC/
#       SVTC/TM) : Document ID embeds the baseline number - "{name}-{baseline}"
#       once baselined (no dot), or "{name}-{baseline}.{minor}" while draft.

PLANNING_FAMILIES = {"PSAC", "SDP", "SVP", "SCMP", "SQAP"}
# Everything else (SRS, SDS, SCS, SVS, SRD, SDDD, DD, CT, SUTC, SVTC, TM, ...)
# uses the "standards" convention by default.


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        dal_level TEXT DEFAULT 'A',
        status TEXT DEFAULT 'in_progress',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS artifacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        module TEXT NOT NULL,
        type TEXT NOT NULL,
        content TEXT,
        file_path TEXT,
        version TEXT DEFAULT '1.0',
        baseline_number INTEGER DEFAULT 1,
        minor_number INTEGER DEFAULT 0,
        status TEXT DEFAULT 'DRAFT',
        change_description TEXT,
        baselined_at TEXT,
        baselined_by TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        module TEXT NOT NULL,
        artifact_type TEXT,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        reviewer TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        target TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS tc_remarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        module TEXT NOT NULL,
        document TEXT NOT NULL,
        req_id TEXT,
        remark TEXT NOT NULL,
        reviewer TEXT,
        status TEXT DEFAULT 'open',
        model_response TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )""")
    conn.commit()
    conn.close()


def migrate_db():
    """Run any needed DB migrations. Safe to call every startup - each
    step checks before acting."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("PRAGMA table_info(tc_remarks)")
    tc_cols = {row[1] for row in c.fetchall()}
    if "reviewer" not in tc_cols:
        c.execute("ALTER TABLE tc_remarks ADD COLUMN reviewer TEXT")
        conn.commit()
        print("✅ DB migrated: tc_remarks.reviewer added")

    c.execute("PRAGMA table_info(artifacts)")
    cols = {row[1]: row[2] for row in c.fetchall()}

    if cols.get('version') == 'INTEGER':
        c.executescript("""
            BEGIN;
            ALTER TABLE artifacts RENAME TO artifacts_old;
            CREATE TABLE artifacts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id  INTEGER NOT NULL,
                module      TEXT    NOT NULL,
                type        TEXT    NOT NULL,
                content     TEXT,
                file_path   TEXT,
                version     TEXT    DEFAULT '1.0',
                created_at  TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            INSERT INTO artifacts
                (id, project_id, module, type, content, file_path, version, created_at)
            SELECT
                id, project_id, module, type, content,
                COALESCE(file_path,''),
                CAST(version AS TEXT) || '.0',
                created_at
            FROM artifacts_old;
            DROP TABLE artifacts_old;
            COMMIT;
        """)
        print("✅ DB migrated: artifacts.version INTEGER → TEXT")
        c.execute("PRAGMA table_info(artifacts)")
        cols = {row[1]: row[2] for row in c.fetchall()}

    new_cols = {
        "baseline_number":     "INTEGER DEFAULT 1",
        "minor_number":        "INTEGER DEFAULT 0",
        "status":              "TEXT DEFAULT 'DRAFT'",
        "change_description":  "TEXT",
        "baselined_at":        "TEXT",
        "baselined_by":        "TEXT",
    }
    added = []
    for col, decl in new_cols.items():
        if col not in cols:
            c.execute(f"ALTER TABLE artifacts ADD COLUMN {col} {decl}")
            added.append(col)
    if added:
        # Best-effort backfill from the legacy 'version' text column
        # (format "N.M") so existing rows aren't all reset to 1.0.
        c.execute("SELECT id, version FROM artifacts WHERE version LIKE '%.%'")
        for row in c.fetchall():
            try:
                major, minor = row["version"].split(".", 1)
                c.execute(
                    "UPDATE artifacts SET baseline_number=?, minor_number=? WHERE id=?",
                    (int(major), int(minor), row["id"])
                )
            except (ValueError, AttributeError):
                continue
        conn.commit()
        print(f"✅ DB migrated: artifacts columns added: {', '.join(added)}")

    conn.close()


def create_project(name, dal_level="A"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO projects (name, dal_level) VALUES (?, ?)", (name, dal_level))
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_all_projects():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM projects ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project(project_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


# ── PERSISTED ACTIVE PROJECT ──────────────────────────────────────────────────
# The custom HTML navigation can trigger a full page navigation. Persisting the
# active project in SQLite makes the selected project survive page changes,
# reruns and returns to the home dashboard.
def _ensure_app_state_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS app_state (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")


def _ensure_project_runtime_table(conn):
    """Create the small runtime-settings table used to keep page context
    coherent for a project (for example the Colab/ngrok URL)."""
    conn.execute("""CREATE TABLE IF NOT EXISTS project_runtime (
        project_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT,
        updated_at TEXT DEFAULT (datetime('now')),
        PRIMARY KEY (project_id, key),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )""")


def set_project_runtime_value(project_id, key, value):
    conn = get_connection()
    _ensure_project_runtime_table(conn)
    conn.execute(
        "INSERT INTO project_runtime(project_id, key, value, updated_at) "
        "VALUES(?, ?, ?, datetime('now')) "
        "ON CONFLICT(project_id, key) DO UPDATE SET "
        "value=excluded.value, updated_at=datetime('now')",
        (int(project_id), str(key), "" if value is None else str(value)),
    )
    conn.commit()
    conn.close()


def get_project_runtime_value(project_id, key, default=None):
    conn = get_connection()
    _ensure_project_runtime_table(conn)
    row = conn.execute(
        "SELECT value FROM project_runtime WHERE project_id=? AND key=?",
        (int(project_id), str(key)),
    ).fetchone()
    conn.close()
    return row["value"] if row else default


def clear_project_runtime(project_id):
    conn = get_connection()
    _ensure_project_runtime_table(conn)
    conn.execute("DELETE FROM project_runtime WHERE project_id=?", (int(project_id),))
    conn.commit()
    conn.close()


def set_active_project_id(project_id):
    conn = get_connection()
    _ensure_app_state_table(conn)
    conn.execute(
        "INSERT INTO app_state(key, value) VALUES('active_project_id', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(project_id),),
    )
    conn.commit()
    conn.close()


def clear_active_project_id():
    conn = get_connection()
    _ensure_app_state_table(conn)
    conn.execute("DELETE FROM app_state WHERE key='active_project_id'")
    conn.commit()
    conn.close()


def get_active_project_persisted():
    conn = get_connection()
    _ensure_app_state_table(conn)
    row = conn.execute(
        "SELECT value FROM app_state WHERE key='active_project_id'"
    ).fetchone()
    conn.close()
    if not row:
        return None
    try:
        project_id = int(row["value"])
    except (TypeError, ValueError):
        clear_active_project_id()
        return None
    project = get_project(project_id)
    if project is None:
        clear_active_project_id()
    return project


def update_project_status(project_id, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE projects SET status=?, updated_at=datetime('now') WHERE id=?", (status, project_id))
    conn.commit()
    conn.close()


def delete_project(project_id):
    conn = get_connection()
    _ensure_app_state_table(conn)
    _ensure_project_runtime_table(conn)
    c = conn.cursor()
    for table in ["tc_remarks", "chat_history", "reviews", "artifacts", "project_runtime"]:
        c.execute(f"DELETE FROM {table} WHERE project_id=?", (project_id,))
    c.execute(
        "DELETE FROM app_state WHERE key='active_project_id' AND value=?",
        (str(project_id),),
    )
    c.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()
    conn.close()


# ── DOCUMENT ID / VERSION FORMATTING ────────────────────────────────────────
def format_doc_id(family: str, baseline_number: int, minor_number: int, status: str) -> str:
    """The single source of truth for how an artifact's Document ID is
    displayed, so it can never drift from its Version/Status again.
    Planning docs (PSAC, SDP, SVP, SCMP, SQAP): bare name always.
    Everything else: "{family}-{baseline}" once BASELINE (no dot),
    "{family}-{baseline}.{minor}" while DRAFT."""
    if family in PLANNING_FAMILIES:
        return family
    if status == "BASELINE":
        return f"{family}-{baseline_number}"
    return f"{family}-{baseline_number}.{minor_number}"


def format_version(baseline_number: int, minor_number: int) -> str:
    """Version field is always "{baseline}.{minor}" regardless of family -
    this is what changes in the cover-page Version cell."""
    return f"{baseline_number}.{minor_number}"


# ── ARTIFACT VERSIONING ─────────────────────────────────────────────────────
def get_next_version(project_id: int, module: str, artifact_type: str = None) -> dict:
    """Compute the (baseline_number, minor_number, status) for the NEXT
    artifact to be generated for this project/module[/type].

    Rule (confirmed): generation NEVER produces a BASELINE - only the
    explicit baseline_artifact() action (the 🔒 button) does, and THAT is
    the only place baseline_number increments. A regular new draft always
    continues the CURRENT baseline number with minor+1, whether the last
    row was itself a DRAFT or a BASELINE (e.g. PDS 2.0 BASELINE -> next
    draft is 2.1, not 3.0 - the baseline number only moves again at the
    next 🔒 click, e.g. SRS-1.6 DRAFT -> 🔒 -> SRS-2 BASELINE).
      - no prior row -> baseline=1, minor=0, DRAFT
      - prior row (DRAFT or BASELINE) -> same baseline, minor+1, DRAFT
    """
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT * FROM artifacts WHERE project_id=? AND module=?"
    params = [project_id, module]
    if artifact_type:
        query += " AND type=?"
        params.append(artifact_type)
    query += " ORDER BY baseline_number DESC, minor_number DESC, id DESC LIMIT 1"
    c.execute(query, params)
    row = c.fetchone()
    conn.close()

    if row is None:
        return {"baseline_number": 1, "minor_number": 0, "status": "DRAFT"}
    return {"baseline_number": row["baseline_number"], "minor_number": row["minor_number"] + 1, "status": "DRAFT"}


def save_artifact(project_id: int, module: str, artifact_type: str,
                  content: str, file_path: str = "",
                  version: dict = None, change_description: str = "") -> int:
    """Save a new artifact version. `version` is the dict returned by
    get_next_version() - if not given, it's computed automatically so
    callers never have to hand-track baseline/minor numbers themselves."""
    if version is None:
        version = get_next_version(project_id, module, artifact_type)

    baseline_number = version["baseline_number"]
    minor_number = version["minor_number"]
    status = version.get("status", "DRAFT")
    version_str = format_version(baseline_number, minor_number)

    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO artifacts
           (project_id, module, type, content, file_path, version,
            baseline_number, minor_number, status, change_description)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (project_id, module, artifact_type, content, file_path, version_str,
         baseline_number, minor_number, status, change_description)
    )
    artifact_id = c.lastrowid
    conn.commit()
    conn.close()
    return artifact_id


def baseline_artifact(artifact_id: int, change_description: str, baselined_by: str = "") -> int:
    """The 🔒 Baseline button: freezes the CURRENT latest draft of one
    artifact as the next baseline. This is the ONLY place baseline_number
    increments (confirmed rule: SRS-1.6 DRAFT -> 🔒 -> SRS-2 BASELINE).
    Creates a NEW row (never mutates the draft it's based on, keeping
    full history) with baseline_number+1, minor reset to 0, status=BASELINE.
    Returns the new artifact id."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,))
    src = c.fetchone()
    if src is None:
        conn.close()
        raise ValueError(f"No artifact with id={artifact_id}")
    if src["status"] == "BASELINE":
        conn.close()
        raise ValueError("This artifact is already a BASELINE - baseline the next draft instead.")

    new_baseline_number = src["baseline_number"] + 1
    new_version_str = format_version(new_baseline_number, 0)
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute(
        """INSERT INTO artifacts
           (project_id, module, type, content, file_path, version,
            baseline_number, minor_number, status, change_description,
            baselined_at, baselined_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'BASELINE', ?, ?, ?)""",
        (src["project_id"], src["module"], src["type"], src["content"],
         src["file_path"], new_version_str, new_baseline_number,
         change_description, now, baselined_by)
    )
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_artifacts(project_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM artifacts WHERE project_id=? ORDER BY module", (project_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_artifact_by_module(project_id, module, artifact_type: str = None):
    """Latest version of an artifact. Sorts numerically on
    (baseline_number, minor_number) - the old version fixed this bug
    where TEXT sort put "10.0" before "2.0"."""
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT * FROM artifacts WHERE project_id=? AND module=?"
    params = [project_id, module]
    if artifact_type:
        query += " AND type=?"
        params.append(artifact_type)
    query += " ORDER BY baseline_number DESC, minor_number DESC, id DESC LIMIT 1"
    c.execute(query, params)
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_artifact_history(project_id, module, artifact_type: str = None):
    """All versions of an artifact, oldest first - for the diff view
    before confirming a baseline."""
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT * FROM artifacts WHERE project_id=? AND module=?"
    params = [project_id, module]
    if artifact_type:
        query += " AND type=?"
        params.append(artifact_type)
    query += " ORDER BY baseline_number ASC, minor_number ASC, id ASC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_baselines(project_id=None):
    """Every BASELINE row, across one project or the whole database -
    feeds the SCMP SCI Register automatically instead of it being
    hand-typed."""
    conn = get_connection()
    c = conn.cursor()
    if project_id is not None:
        c.execute(
            "SELECT * FROM artifacts WHERE project_id=? AND status='BASELINE' "
            "ORDER BY baselined_at ASC", (project_id,)
        )
    else:
        c.execute("SELECT * FROM artifacts WHERE status='BASELINE' ORDER BY baselined_at ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_review(project_id, module, artifact_type, status, notes, reviewer=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO reviews (project_id, module, artifact_type, status, notes, reviewer) VALUES (?, ?, ?, ?, ?, ?)",
              (project_id, module, artifact_type, status, notes, reviewer))
    rid = c.lastrowid
    conn.commit()
    conn.close()
    return rid


def get_reviews(project_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM reviews WHERE project_id=? ORDER BY created_at DESC", (project_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_chat(project_id, target, question, answer):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (project_id, target, question, answer) VALUES (?, ?, ?, ?)",
              (project_id, target, question, answer))
    cid = c.lastrowid
    conn.commit()
    conn.close()
    return cid


def get_chat_history(project_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM chat_history WHERE project_id=? ORDER BY created_at", (project_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_tc_remark(project_id, module, document, req_id, remark, reviewer=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO tc_remarks (project_id, module, document, req_id, remark, reviewer) VALUES (?, ?, ?, ?, ?, ?)",
              (project_id, module, document, req_id, remark, reviewer))
    tid = c.lastrowid
    conn.commit()
    conn.close()
    return tid


def delete_tc_remark(tc_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tc_remarks WHERE id=?", (tc_id,))
    conn.commit()
    conn.close()


def get_tc_remarks(project_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tc_remarks WHERE project_id=? ORDER BY module", (project_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_tc_status(tc_id, status, model_response=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tc_remarks SET status=?, model_response=? WHERE id=?",
              (status, model_response, tc_id))
    conn.commit()
    conn.close()


init_db()
migrate_db()