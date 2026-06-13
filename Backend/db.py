import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "isceet.db")


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
        version INTEGER DEFAULT 1,
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
        status TEXT DEFAULT 'open',
        model_response TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )""")
    conn.commit()
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
    c.execute("SELECT * FROM projects ORDER BY created_at DESC")
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


def update_project_status(project_id, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE projects SET status=?, updated_at=datetime('now') WHERE id=?", (status, project_id))
    conn.commit()
    conn.close()


def delete_project(project_id):
    conn = get_connection()
    c = conn.cursor()
    for table in ["tc_remarks", "chat_history", "reviews", "artifacts"]:
        c.execute(f"DELETE FROM {table} WHERE project_id=?", (project_id,))
    c.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()
    conn.close()


def save_artifact(project_id, module, artifact_type, content, file_path=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO artifacts (project_id, module, type, content, file_path) VALUES (?, ?, ?, ?, ?)",
              (project_id, module, artifact_type, content, file_path))
    aid = c.lastrowid
    conn.commit()
    conn.close()
    return aid


def get_artifacts(project_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM artifacts WHERE project_id=? ORDER BY module", (project_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_artifact_by_module(project_id, module):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM artifacts WHERE project_id=? AND module=? ORDER BY version DESC LIMIT 1",
              (project_id, module))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


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


def save_tc_remark(project_id, module, document, req_id, remark):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO tc_remarks (project_id, module, document, req_id, remark) VALUES (?, ?, ?, ?, ?)",
              (project_id, module, document, req_id, remark))
    tid = c.lastrowid
    conn.commit()
    conn.close()
    return tid


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