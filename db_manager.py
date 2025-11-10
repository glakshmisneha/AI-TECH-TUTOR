import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

DB_NAME = 'ds_tutor.db'

# --- Initialization & Utility ---

def init_db():
    # Only create the database file if it doesn't exist.
    # We skip the user population for production deployment's first run 
    # but keep the table creation logic.
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
            name TEXT NOT NULL, level TEXT DEFAULT 'unassigned', score INTEGER DEFAULT 0,
            quiz_status TEXT DEFAULT 'pending_pre'
        )
    """)
    c.execute("""
      CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY, email TEXT NOT NULL, level TEXT NOT NULL,
        lesson_index INTEGER DEFAULT 0, UNIQUE(email, level)
      )
    """)

    # --- Seed Test Users (for initial local setup) ---
    c.execute("SELECT * FROM users WHERE email='user@ai.com'")
    if c.fetchone() is None:
        c.execute("INSERT INTO users (email, password, name, level, score, quiz_status) VALUES (?, ?, ?, ?, ?, ?)",
                  ('user@ai.com', generate_password_hash('12345'), 'Tech Tutor User', 'unassigned', 0, 'pending_pre'))
        c.execute("INSERT INTO users (email, password, name, level, score, quiz_status) VALUES (?, ?, ?, ?, ?, ?)",
                  ('alice@test.com', generate_password_hash('pass123'), 'Alice Smith', 'medium', 6, 'completed_easy'))
        c.execute("INSERT INTO users (email, password, name, level, score, quiz_status) VALUES (?, ?, ?, ?, ?, ?)",
                  ('bob@test.com', generate_password_hash('pass123'), 'Bob Johnson', 'advance', 9, 'completed_medium'))
        c.execute("INSERT INTO users (email, password, name, level, score, quiz_status) VALUES (?, ?, ?, ?, ?, ?)",
                  ('chloe@test.com', generate_password_hash('pass123'), 'Chloe Lee', 'easy', 3, 'completed_pre'))
    # -------------------------------------------------

    conn.commit()
    conn.close()

# Initialize the database file
if not os.path.exists(DB_NAME):
    init_db()

# --- CRUD Functions ---

def get_user_by_email(email):
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    c = conn.cursor(); c.execute("SELECT * FROM users WHERE email=?", (email,))
    r = c.fetchone(); conn.close()
    return dict(r) if r else None

def add_new_user(email, hashed_pw, name):
    try:
        conn = sqlite3.connect(DB_NAME); c = conn.cursor()
        c.execute("INSERT INTO users (email, password, name, level, quiz_status) VALUES (?, ?, ?, ?, 'pending_pre')",
                  (email, hashed_pw, name, 'unassigned'))
        conn.commit(); conn.close(); return True
    except sqlite3.IntegrityError:
        conn.close(); return False

def update_user_quiz_result(email, level, score, quiz_status):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("UPDATE users SET level=?, score=?, quiz_status=? WHERE email=?",
              (level, score, quiz_status, email))
    if level != 'unassigned':
      c.execute("""
          INSERT INTO user_progress(email, level, lesson_index) VALUES(?,?,0)
          ON CONFLICT(email, level) DO UPDATE SET lesson_index=0
          WHERE excluded.level != user_progress.level
      """, (email, level))
    conn.commit(); conn.close()

def get_user_quiz_status(email):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("SELECT quiz_status FROM users WHERE email=?", (email,))
    status = c.fetchone()
    conn.close()
    return status[0] if status else 'pending_pre'

def get_all_users_by_score():
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
    c = conn.cursor(); c.execute("SELECT name, level, score, email, quiz_status FROM users ORDER BY score DESC, name ASC")
    users = [dict(r) for r in c.fetchall()]; conn.close(); return users

def get_progress(email, level):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("SELECT lesson_index FROM user_progress WHERE email=? AND level=?", (email, level))
    r = c.fetchone()
    if r is None:
        c.execute("INSERT INTO user_progress(email,level,lesson_index) VALUES(?,?,0)", (email, level))
        conn.commit(); idx = 0
    else:
        idx = r[0]
    conn.close()
    return idx

def set_progress(email, level, index):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("""
      INSERT INTO user_progress(email,level,lesson_index) VALUES(?,?,?)
      ON CONFLICT(email,level) DO UPDATE SET lesson_index=excluded.lesson_index
    """, (email, level, index))
    conn.commit(); conn.close()
