import os
import sqlite3
import re
import json
from urllib.parse import urlencode
from flask import Flask, request, redirect, url_for, session, get_flashed_messages, jsonify
from jinja2 import DictLoader, Environment
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai
from google.genai.errors import APIError

# ==============================================================================
# 1. Configuration and Security Setup (Env Vars and DB) 🔒
# ==============================================================================

DB_NAME = 'ds_tutor.db'
PASSWORD_MIN_LENGTH = 8
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# 🚨 IMPORTANT: Reading secrets from environment variables
try:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    FLASK_SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key_if_none_set')

    if not GEMINI_API_KEY:
        # In deployment, this error stops the service, flagging the missing key
        print("❌ CONFIGURATION ERROR: GEMINI_API_KEY not found in environment variables.")
        raise SystemExit("Missing Environment Variable: GEMINI_API_KEY")

    client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL = 'gemini-2.5-flash'

except Exception as e:
    # Log any other initialization error
    print(f"❌ CONFIGURATION ERROR: Failed to initialize client: {e}")
    raise

# ==============================================================================
# 2. Database Functions (SQLite) 💾
# ==============================================================================

def init_db():
    # SQLite is used here for simplicity, but for Vercel/production, this data is ephemeral.
    # A persistent database (like PostgreSQL) is required for permanent data storage.
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

    # Insert test users if they don't exist
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

    conn.commit()
    conn.close()

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

init_db()

# ==============================================================================
# 3. Data Store, Quiz Answers, and Gemini Helpers - LEVEL-SPECIFIC QUIZ DATA
# ==============================================================================

QUIZ_ANSWERS = { "q1": "A", "q2": "B", "q3": "C", "q4": "A", "q5": "B", "q6": "C", "q7": "A", "q8": "B", "q9": "C", "q10": "A" }

LESSONS = {
    'easy': [
        {"title":"Arrays — Indexing, Access & Complexity", "url":"https://www.youtube.com/embed/QJNwK2uJyGs", "desc":"Intro to arrays: indexing, O(1) access."},
        {"title":"Linked Lists — Nodes & Pointers", "url":"https://www.youtube.com/embed/WwfhLC16bis", "desc":"Singly linked lists: nodes, pointers, traversal, tradeoffs."},
        {"title":"Stacks — LIFO Structure", "url":"https://www.youtube.com/embed/wjI1WNcIntg", "desc":"Stack basics: push, pop, peek, LIFO."},
        {"title":"Queues — FIFO Structure", "url":"https://www.youtube.com/embed/zp6pBNbUB2U", "desc":"Queues: enqueue/dequeue, FIFO structure."},
    ],
    'medium': [
        {"title":"Binary Trees — Structure & Traversals", "url":"https://www.youtube.com/embed/H5JubkIy_p8", "desc":"Binary trees: nodes, height, recursion, traversals."},
        {"title":"Binary Search Trees — Operations", "url":"https://www.youtube.com/embed/5cPbNCrdotA", "desc":"BST invariant, search/insert/delete, complexity."},
    ],
    'advance': [
        {"title":"Graph Theory — Fundamentals (Course)", "url":"https://www.youtube.com/embed/09_LlHjoEiY", "desc":"Graphs: vertices/edges, adjacency list/matrix."},
        {"title":"Graph Traversal — BFS", "url":"https://www.youtube.com/embed/pcKY4hjDrxk", "desc":"BFS with queue, levels, shortest path in unweighted graphs."},
    ]
}

EASY_FINAL_QUIZ_QUESTIONS = {
    "q1": {"q":"What is the worst-case complexity for insertion into a full dynamic array?", "a":["O(1)", "O(log n)", "O(n)"], "opts":["O(1)", "O(log n)", "O(n)"], "correct": "O(n)"},
    "q2": {"q":"Which structure is best for implementing a 'Back' button history in an application?", "a":["Queue", "Linked List", "Stack"], "opts":["Queue", "Linked List", "Stack"], "correct": "Stack"},
    "q3": {"q":"Which data structure uses the FIFO principle?", "a":["Stack", "Queue", "Array"], "opts":["Stack", "Queue", "Array"], "correct": "Queue"},
    "q4": {"q":"Accessing the Nth element of an array takes O(1) time. This is known as:", "a":["Sequential Access", "Random Access", "Linear Access"], "opts":["Sequential Access", "Random Access", "Linear Access"], "correct": "Random Access"},
    "q5": {"q":"In a singly linked list, how do you find the last element?", "a":["Use the tail pointer", "Traverse from the head", "Use the list index"], "opts":["Use the tail pointer", "Traverse from the head", "Use the list index"], "correct": "Traverse from the head"},
    "q6": {"q":"Big O notation O(n) signifies:", "a":["Constant time", "Linear time", "Logarithmic time"], "opts":["Constant time", "Linear time", "Logarithmic time"], "correct": "Linear time"},
    "q7": {"q":"The main advantage of a linked list over an array is:", "a":["Faster search time", "Faster random access", "Dynamic size and easier insertion/deletion"], "opts":["Faster search time", "Faster random access", "Dynamic size and easier insertion/deletion"], "correct": "Dynamic size and easier insertion/deletion"},
    "q8": {"q":"What operation removes an element from the front of a queue?", "a":["Push", "Pop", "Dequeue"], "opts":["Push", "Pop", "Dequeue"], "correct": "Dequeue"},
    "q9": {"q":"The main disadvantage of a stack is that it does not support:","a":["LIFO", "Push/Pop operations", "Random access to elements"], "opts":["LIFO", "Push/Pop operations", "Random access to elements"], "correct": "Random access to elements"},
    "q10": {"q":"Time complexity for pushing an element onto a stack is typically:", "a":["O(n)", "O(1)", "O(log n)"], "opts":["O(n)", "O(1)", "O(log n)"], "correct": "O(1)"},
}

MEDIUM_FINAL_QUIZ_QUESTIONS = {
    "q1": {"q":"Which traversal visits nodes in the order: Left, Root, Right?", "a":["Pre-order", "In-order", "Post-order"], "opts":["Pre-order", "In-order", "Post-order"], "correct": "In-order"},
    "q2": {"q":"A BST's efficiency collapses to O(n) in the worst case when the tree is:", "a":["Full", "Complete", "Skewed"], "opts":["Full", "Complete", "Skewed"], "correct": "Skewed"},
    "q3": {"q":"AVL trees maintain balance using:", "a":["Coloring", "Rotations", "Heaps"], "opts":["Coloring", "Rotations", "Heaps"], "correct": "Rotations"},
    "q4": {"q":"What is the maximum number of children a node can have in a Binary Tree?", "a":["One", "Two", "Three"], "opts":["One", "Two", "Three"], "correct": "Two"},
    "q5": {"q":"What is the core condition for a Min Heap?", "a":["Parent > Children", "Parent < Children", "Left < Right"], "opts":["Parent > Children", "Parent < Children", "Left < Right"], "correct": "Parent < Children"},
    "q6": {"q":"The call stack is crucial to understanding which concept?", "a":["Iteration", "Recursion", "Hashing"], "opts":["Iteration", "Recursion", "Hashing"], "correct": "Recursion"},
    "q7": {"q":"Finding the smallest element in a Min Heap takes how much time?", "a":["O(n)", "O(log n)", "O(1)"], "opts":["O(n)", "O(log n)", "O(1)"], "correct": "O(1)"},
    "q8": {"q":"A node with no children is called a:", "a":["Root", "Internal Node", "Leaf Node"], "opts":["Root", "Internal Node", "Leaf Node"], "correct": "Leaf Node"},
    "q9": {"q":"What is the function of a 'base case' in recursion?", "a":["To skip a step", "To define the goal", "To stop the recursion"], "opts":["To skip a step", "To define the goal", "To stop the recursion"], "correct": "To stop the recursion"},
    "q10": {"q":"The process of re-ordering elements in a heap after insertion or deletion is called:", "a":["Traversing", "Heapifying", "Balancing"], "opts":["Traversing", "Heapifying", "Balancing"], "correct": "Heapifying"},
}

ADVANCE_FINAL_QUIZ_QUESTIONS = {
    "q1": {"q":"Depth-First Search (DFS) typically uses which data structure?", "a":["Queue", "Priority Queue", "Stack"], "opts":["Queue", "Priority Queue", "Stack"], "correct": "Stack"},
    "q2": {"q":"Which graph representation wastes space for sparse graphs?", "a":["Adjacency List", "Adjacency Matrix", "Edge List"], "opts":["Adjacency List", "Adjacency Matrix", "Edge List"], "correct": "Adjacency Matrix"},
    "q3": {"q":"Dijkstra's algorithm cannot handle edges with:", "a":["Zero weight", "Positive weight", "Negative weight"], "opts":["Zero weight", "Positive weight", "Negative weight"], "correct": "Negative weight"},
    "q4": {"q":"BFS is guaranteed to find the shortest path in an unweighted graph.", "a":["True", "False"], "opts":["True", "False"], "correct": "True"},
    "q5": {"q":"The two key properties of Dynamic Programming are Optimal Substructure and:", "a":["Greedy Choice Property", "Recursion", "Overlapping Subproblems"], "opts":["Greedy Choice Property", "Recursion", "Overlapping Subproblems"], "correct": "Overlapping Subproblems"},
    "q6": {"q":"What term describes when a directed graph has no cycles?", "a":["Weighted", "Connected", "Acyclic"], "opts":["Weighted", "Connected", "Acyclic"], "correct": "Acyclic"},
    "q7": {"q":"What is the time complexity of BFS on a graph represented by an Adjacency List?", "a":["O(V+E)", "O(V^2)", "O(E log V)"], "opts":["O(V+E)", "O(V^2)", "O(E log V)"], "correct": "O(V+E)"},
    "q8": {"q":"In DP, storing results of subproblems to avoid re-calculation is called:", "a":["Tabulation", "Memoization", "Recursion"], "opts":["Tabulation", "Memoization", "Recursion"], "correct": "Memoization"},
    "q9": {"q":"The maximum number of edges in a graph with V vertices is roughly:", "a":["V", "V log V", "V^2"], "opts":["V", "V log V", "V^2"], "correct": "V^2"},
    "q10": {"q":"The core idea of Memoization is:", "a":["Solving the largest problem first", "Storing results of expensive function calls", "Using a priority queue"], "opts":["Solving the largest problem first", "Storing results of expensive function calls", "Using a priority queue"], "correct": "Storing results of expensive function calls"},
    "q11": {"q":"Bellman-Ford algorithm can detect the presence of:", "a":["Negative cycles", "Positive cycles", "Self-loops"], "opts":["Negative cycles", "Positive cycles", "Self-loops"], "correct": "Negative cycles"},
    "q12": {"q":"What sorting algorithm has a worst-case time complexity of O(n log n)?", "a":["Quick Sort", "Insertion Sort", "Merge Sort"], "opts":["Quick Sort", "Insertion Sort", "Merge Sort"], "correct": "Merge Sort"},
    "q13": {"q":"Which data structure is typically used to implement a Min/Max Heap?", "a":["Linked List", "Array", "Hash Table"], "opts":["Linked List", "Array", "Hash Table"], "correct": "Array"},
    "q14": {"q":"A hash function's main goal is to minimize:", "a":["Array size", "Collisions", "Load factor"], "opts":["Array size", "Collisions", "Load factor"], "correct": "Collisions"},
    "q15": {"q":"Prim's algorithm and Kruskal's algorithm are used to find the:", "a":["Shortest path", "Maximum flow", "Minimum Spanning Tree"], "opts":["Shortest path", "Maximum flow", "Minimum Spanning Tree"], "correct": "Minimum Spanning Tree"},
    "q16": {"q":"What is a 'Cut' in Max Flow / Min Cut theory?", "a":["A cycle in the graph", "A partition of vertices", "An isolated vertex"], "opts":["A cycle in the graph", "A partition of vertices", "An isolated vertex"], "correct": "A partition of vertices"},
    "q17": {"q":"The 'master theorem' is most commonly used for analyzing the complexity of:", "a":["Iterative algorithms", "Recursive algorithms", "Graph algorithms"], "opts":["Iterative algorithms", "Recursive algorithms", "Graph algorithms"], "correct": "Recursive algorithms"},
    "q18": {"q":"What method is used in DP to fill a table from the smallest subproblems up to the main problem?", "a":["Memoization", "Top-down", "Tabulation"], "opts":["Memoization", "Top-down", "Tabulation"], "correct": "Tabulation"},
    "q19": {"q":"What's the best time complexity for searching a balanced Binary Search Tree (e.g., AVL, Red-Black)?", "a":["O(n)", "O(log n)", "O(1)"], "opts":["O(n)", "O(log n)", "O(1)"], "correct": "O(log n)"},
    "q20": {"q":"The main advantage of using a Trie (Prefix Tree) is its efficiency in:", "a":["Sorting numbers", "String matching and searching", "Managing network routing"], "opts":["Sorting numbers", "String matching and searching", "Managing network routing"], "correct": "String matching and searching"},
}

def create_answer_map(quiz_dict):
    return {q_num: data['correct'] for q_num, data in quiz_dict.items()}

LEVEL_QUIZ_MAP = {
    'easy': {'questions': EASY_FINAL_QUIZ_QUESTIONS, 'total': len(EASY_FINAL_QUIZ_QUESTIONS), 'pass_threshold': 8, 'correct_answers': create_answer_map(EASY_FINAL_QUIZ_QUESTIONS)},
    'medium': {'questions': MEDIUM_FINAL_QUIZ_QUESTIONS, 'total': len(MEDIUM_FINAL_QUIZ_QUESTIONS), 'pass_threshold': 8, 'correct_answers': create_answer_map(MEDIUM_FINAL_QUIZ_QUESTIONS)},
    'advance': {'questions': ADVANCE_FINAL_QUIZ_QUESTIONS, 'total': len(ADVANCE_FINAL_QUIZ_QUESTIONS), 'pass_threshold': 16, 'correct_answers': create_answer_map(ADVANCE_FINAL_QUIZ_QUESTIONS)},
}

def generate_video_summary(level, desc):
    prompt = (
        f"Generate a concise, engaging, two-sentence summary for a {level.title()} "
        f"level Data Structures video. The lesson description is: {desc}. "
        "Also, pull out ONE bold key concept from the provided content, making sure the entire response is under 80 words."
    )
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text
    except APIError as e:
        return f"Gemini Error: Could could not generate summary. ({e})"
    except Exception:
        return "Error: Failed to connect to AI service."

# ==============================================================================
# 4. Flask App and Templates Initialization 🌐
# ==============================================================================

# 🚨 IMPORTANT: The Flask instance must be named 'app' for Vercel/Gunicorn to find it.
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# All HTML Template Strings are defined below (omitted for brevity here, but included
# in the full file). The template rendering function remains the same.

BASE_HTML = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AI TECH TUTOR</title><style>
:root{--primary-dark:#1e143f;--secondary-dark:#2c1e55;--accent-pink:#ff3399;--accent-blue:#00ffff;--text-light:#e2e8f0;--ok:#22c55e;--warn:#dc2626;--muted:#94a3b8;}
*{box-sizing:border-box}body{margin:0;background:var(--primary-dark);color:var(--text-light);font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto}
h1,h2,h3{margin:0 0 .5rem}a{color:var(--accent-pink);text-decoration:none}
.container{display:flex;min-height:100vh}
.sidebar{width:260px;background:var(--primary-dark);color:var(--text-light);display:flex;flex-direction:column;border-right:1px solid rgba(255,255,255,0.1);}
.sidebar h2{padding:20px;font-size:1.4rem;border-bottom:1px solid rgba(255,255,255,0.1);}
.nav a{display:block;padding:14px 20px;color:var(--muted);font-weight:500;}
.nav a.active,.nav a:hover{background:var(--secondary-dark);color:var(--text-light);border-left:4px solid var(--accent-pink)}
.content{flex:1;padding:32px;background:var(--secondary-dark);}
.card{background:rgba(255,255,255,0.05);border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.3);padding:24px;margin-bottom:20px;border:1px solid rgba(255,255,255,0.1);}
.btn{display:inline-block;background:var(--accent-pink);color:#fff;border:none;border-radius:6px;padding:10px 16px;font-weight:600;cursor:pointer;transition:.2s;box-shadow:0 0 10px rgba(255,51,153,0.5);}
.btn:hover{background:#d32b80;transform:translateY(-1px);box-shadow:0 0 15px rgba(255,51,153,0.7);}
.btn[disabled]{opacity:.4;cursor:not-allowed;box-shadow:none;}
.input{width:100%;padding:10px 12px;border:1px solid rgba(255,255,255,0.3);border-radius:6px;background:rgba(0,0,0,0.2);color:var(--text-light);font-size:1rem;}
.input::placeholder{color:rgba(255,255,255,0.5);}
.input:focus{outline:none;border-color:var(--accent-blue);box-shadow:0 0 8px rgba(0,255,255,0.5);}
.row{display:flex;gap:10px;align-items:center;}
.error{color:var(--warn);font-size:.9rem;font-weight:500;}
.hint{color:var(--muted);font-size:.9rem;}
.progress{background:rgba(255,255,255,0.1);border-radius:10px;height:12px;overflow:hidden}
.progress>div{height:100%;background:var(--ok)}
.chat{border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:16px;background:rgba(0,0,0,0.2);box-shadow:0 4px 10px rgba(0,0,0,.3);}
.bubble{padding:10px 14px;border-radius:16px;max-width:85%;box-shadow:0 1px 3px rgba(0,0,0,.15);margin-bottom:10px;font-size:0.95rem;}
.bubble.user{background:var(--accent-pink);color:#fff;margin-left:auto;border-bottom-right-radius:4px}
.bubble.ai{background:#2c1e55;color:var(--text-light);border-bottom-left-radius:4px;border: 1px solid rgba(255,255,255,0.1);}
.badge{font-size:.75rem;color:var(--accent-blue);font-weight:600;}
</style></head><body>{% block content %}{% endblock %}</body></html>
"""

LOGIN_HTML = r"""{% extends 'BASE_HTML' %}{% block content %}
<style>
    .login-container{display:flex;height:100vh;max-width:1400px;margin:0 auto;}
    .login-form-wrapper{width:35%;max-width:400px;padding:50px;display:flex;flex-direction:column;justify-content:center;color:var(--text-light);background:var(--primary-dark);}
    .login-visual-area{flex:1;background:var(--secondary-dark);display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;}
    .login-title{font-size:2.5rem;font-weight:700;color:var(--text-light);margin-bottom:10px;}
    .input-group{margin-bottom:15px;position:relative;}
    .input-icon{position:absolute;top:10px;left:12px;color:var(--muted);font-size:1.1rem;z-index:10;}
    .input{padding-left:35px !important; color:var(--text-light);}
    .input::placeholder{color:rgba(255,255,255,0.5);}
    .form-header{text-align:center;margin-bottom:50px;}
    .form-header svg{width:80px;height:80px;color:var(--accent-pink);margin-bottom:15px;}
    .visual-wave-text{color:var(--text-light);font-size:4rem;font-weight:800;}
    .wave-bg{position:absolute;width:100%;height:100%;background:radial-gradient(circle at 70% 30%, rgba(255, 51, 153, 0.4) 0%, transparent 20%), radial-gradient(circle at 40% 60%, rgba(0, 255, 255, 0.4) 0%, transparent 20%); filter: blur(50px);}
</style>
<div class="login-container">
    <div class="login-form-wrapper">
        <div class="form-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-user-check"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><polyline points="17 11 19 13 23 9"></polyline></svg>
            <h2 style="font-size:1.6rem; color: var(--text-light);">AI Tutor Login</h2>
        </div>

        <form method="POST" novalidate style="width: 100%;">
            <input type="hidden" name="action" value="login">

            <div class="input-group">
                <span class="input-icon">👤</span>
                <input class="input" name="email" type="email" placeholder="USERNAME" required>
            </div>

            <div class="input-group">
                <span class="input-icon">🔒</span>
                <input class="input" name="password" type="password" placeholder="PASSWORD" required>
            </div>

            <div style="display:flex; justify-content:space-between; font-size:0.9rem; margin-bottom: 25px;">
                <label style="color:var(--muted);"><input type="checkbox" style="margin-right:5px;"> Remember me</label>
                <a href="{{ url_for('signup') }}" style="color:var(--muted);">Forgot your password?</a>
            </div>

            <button class="btn auth-btn" style="width:100%; padding: 12px; font-size:1.1rem; text-transform:uppercase;">LOGIN</button>
        </form>

        {% if error %}<div class="error" style="margin-top:15px; text-align:center;">{{ error }}</div>{% endif %}

        <div style="margin-top:40px; text-align:center; font-size:0.95rem;">
            Not a member? <a href="{{ url_for('signup') }}" style="color:var(--accent-blue); font-weight:600;">Sign up here</a>
        </div>
        <div style="margin-top:10px; text-align:center; font-size:0.8rem; color: var(--muted);">Test login: <b>user@ai.com / 12345</b></div>
    </div>

    <div class="login-visual-area">
        <div class="wave-bg"></div>
        <div style="text-align:center; z-index:10;">
            <div class="visual-wave-text">Welcome.</div>
            <p style="color:var(--muted); max-width: 400px; margin-top: 20px;">Unlock your Data Structures journey with personalized AI guidance.</p>
        </div>
    </div>
</div>
{% endblock %}"""

SIGNUP_HTML = r"""{% extends 'BASE_HTML' %}{% block content %}
<style>
    .signup-container{display:flex;height:100vh;max-width:1400px;margin:0 auto;}
    .signup-form-wrapper{width:35%;max-width:400px;padding:50px;display:flex;flex-direction:column;justify-content:center;color:var(--text-light);background:var(--primary-dark);}
    .signup-visual-area{flex:1;background:var(--secondary-dark);display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;}
    .signup-title{font-size:1.6rem;font-weight:700;color:var(--text-light);margin-bottom:10px;}
    .input-group{margin-bottom:15px;position:relative;}
    .input-icon{position:absolute;top:10px;left:12px;color:var(--muted);font-size:1.1rem;z-index:10;}
    .input{padding-left:35px !important; color:var(--text-light);}
    .input::placeholder{color:rgba(255,255,255,0.5);}
    .form-header{text-align:center;margin-bottom:40px;}
    .form-header svg{width:60px;height:60px;color:var(--accent-blue);margin-bottom:10px;}
    .visual-wave-text{color:var(--text-light);font-size:3rem;font-weight:800; text-align: center;}
    .wave-bg{position:absolute;width:100%;height:100%;background:radial-gradient(circle at 20% 80%, rgba(255, 51, 153, 0.4) 0%, transparent 20%), radial-gradient(circle at 60% 30%, rgba(0, 255, 255, 0.4) 0%, transparent 20%); filter: blur(50px);}
    #email-feedback { font-size: 0.85rem; margin-top: 5px; }
    .status-ok { color: var(--ok); }
    .status-error { color: var(--warn); }
</style>
<div class="signup-container">
    <div class="signup-form-wrapper">
        <div class="form-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-user-plus"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
            <h2 class="signup-title">Create Your Account</h2>
        </div>

        <form method="POST" id="signup-form" novalidate style="width: 100%;">
            <input type="hidden" name="action" value="signup">

            <div class="input-group">
                <span class="input-icon">🧑</span>
                <input class="input" name="name" id="name" type="text" placeholder="FULL NAME" required>
            </div>

            <div class="input-group">
                <span class="input-icon">📧</span>
                <input class="input" name="email" id="email" type="email" placeholder="EMAIL ADDRESS" required>
                <div id="email-feedback" class="hint"></div>
            </div>

            <div class="input-group">
                <span class="input-icon">🔒</span>
                <input class="input" name="password" id="password" type="password" placeholder="PASSWORD" required>
                <div id="password-feedback" class="hint">Min 8 chars, ⬆️, ⬇️, 🔢</div>
            </div>

            <button class="btn auth-btn" id="signup-btn" disabled style="width:100%; padding: 12px; font-size:1.1rem; margin-top: 20px;">SIGN UP</button>

            {% if error %}<div class="error" style="margin-top:15px; text-align:center;">{{ error }}</div>{% endif %}
        </form>

        <div style="margin-top:40px; text-align:center; font-size:0.95rem;">
            Already have an account? <a href="{{ url_for('login') }}" style="color:var(--accent-blue); font-weight:600;">Log in here</a>
        </div>
    </div>

    <div class="signup-visual-area">
        <div class="wave-bg"></div>
        <div style="text-align:center; z-index:10;">
            <div class="visual-wave-text">Let's build.</div>
            <p style="color:var(--muted); max-width: 400px; margin-top: 20px;">Mastering data structures is the key to software excellence.</p>
        </div>
    </div>
</div>
<script>
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const signupBtn = document.getElementById('signup-btn');
    const emailFeedback = document.getElementById('email-feedback');
    const passwordFeedback = document.getElementById('password-feedback');
    const nameInput = document.getElementById('name');

    let isEmailValid = false;
    let isPasswordStrong = false;
    let emailCheckTimeout;

    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;

    function validateForm() {
        const isNameFilled = nameInput.value.trim().length > 0;
        signupBtn.disabled = !(isEmailValid && isPasswordStrong && isNameFilled);
    }

    function checkPassword() {
        const password = passwordInput.value;
        const isValid = passwordRegex.test(password);

        isPasswordStrong = isValid;

        if (password.length > 0) {
             if (isValid) {
                passwordFeedback.innerHTML = '<span class="status-ok">Password is strong!</span>';
             } else {
                passwordFeedback.innerHTML = '<span class="status-error">Password must be min 8 chars with upper, lower & digit.</span>';
             }
        } else {
             passwordFeedback.innerHTML = 'Min 8 chars, ⬆️, ⬇️, 🔢';
        }
        validateForm();
    }

    async function checkEmailAvailability() {
        const email = emailInput.value.trim();
        if (!emailRegex.test(email)) {
            emailFeedback.innerHTML = email.length > 0 ? '<span class="status-error">Invalid email format.</span>' : '';
            isEmailValid = false;
            validateForm();
            return;
        }

        emailFeedback.innerHTML = '<span class="hint">Checking availability...</span>';

        try {
            const response = await fetch('/api/check_email?' + new URLSearchParams({ email: email }));
            const data = await response.json();

            if (data.exists) {
                emailFeedback.innerHTML = '<span class="status-error">This email is already registered.</span>';
                isEmailValid = false;
            } else {
                emailFeedback.innerHTML = '<span class="status-ok">Email is available!</span>';
                isEmailValid = true;
            }
        } catch (e) {
            emailFeedback.innerHTML = '<span class="status-error">Error checking email.</span>';
            isEmailValid = false;
        }
        validateForm();
    }

    // --- Event Listeners ---
    nameInput.addEventListener('input', validateForm);

    emailInput.addEventListener('input', () => {
        clearTimeout(emailCheckTimeout);
        emailCheckTimeout = setTimeout(checkEmailAvailability, 500);
    });

    passwordInput.addEventListener('input', checkPassword);

    // Initial calls to set the correct state on page load
    checkPassword();
    checkEmailAvailability();
    validateForm();
</script>
{% endblock %}"""

DASHBOARD_HTML = r"""{% extends 'BASE_HTML' %}{% block content %}
<div class="container">
  <div class="sidebar">
    <h2>AI TECH TUTOR</h2>
    <div class="nav">
      <a href="{{ url_for('dashboard', page='home') }}" class="{% if page=='home' %}active{% endif %}">🏠 Home</a>
      <a href="{{ url_for('dashboard', page='subjects') }}" class="{% if page=='subjects' or page.startswith('ds-') %}active{% endif %}">📚 Learning Path</a>
      <a href="{{ url_for('dashboard', page='scoreboard') }}" class="{% if page=='scoreboard' %}active{% endif %}">🏆 Scoreboard</a>
    </div>
    <div style="margin-top:auto;padding:16px;border-top:1px solid rgba(255,255,255,0.1);">
      <div style="font-weight:600; color:var(--text-light);">👤 {{ user.name }}</div>
      <a class="btn ghost" style="margin-top:10px; padding: 8px 12px; background:rgba(0,0,0,0.2); border-color: var(--accent-pink); color: var(--accent-pink);" href="{{ url_for('logout') }}">Logout</a>
    </div>
  </div>
  <div class="content">
    <h1 style="font-size: 2rem; margin-bottom: 20px; color: var(--text-light);">{{ page.replace('-', ' ').title() }}</h1>
    {% block main_content %}{% endblock %}
  </div>
</div>
{% endblock %}"""

HOME_CONTENT = r"""{% extends 'DASHBOARD_HTML' %}{% block main_content %}
<div class="card">
  <h2>Your Focused Learning Path</h2>
  <ul><li><a href="{{ url_for('dashboard', page='subjects') }}" style="color: var(--accent-blue);"><b>💻 Data Structures</b></a> (Your main learning path)</li></ul>
</div>
<div class="card">
  <h2>Learning Progress</h2>
  {% if user.level == 'unassigned' %}
    <p>You must complete the <b>Pre-Assessment Quiz</b> to determine your starting level.</p>
    <a href="{{ url_for('dashboard', page='ds-quiz') }}" class="btn" style="margin-top:10px;">Start Pre-Assessment Quiz</a>
  {% elif user.quiz_status == 'completed_advance' %}
    <div style="text-align: center; color: var(--ok); padding: 25px; border: 2px solid var(--ok); border-radius: 8px; background: rgba(34, 197, 94, 0.1);">
        <h3 style="color: var(--ok); margin-bottom: 10px;">🎉 Course Completed! 🎉</h3>
        <p>You have successfully mastered all Data Structures content.</p>
        <a href="{{ url_for('dashboard', page='scoreboard') }}" class="btn" style="background: var(--ok); margin-top: 15px; box-shadow: none;">View Final Score</a>
    </div>
  {% else %}
    <p><b>Your Current Level:</b> <span style="text-transform: uppercase; font-weight: 700; color: var(--accent-blue);">{{ user.level }}</span></p>
    <p><b>Lessons Completed:</b> {{ completed }}/{{ total }} ({{ progress_percent }}%)</p>
    <div class="progress"><div style="width: {{ progress_percent }}%"></div></div>

    {% if completed < total %}
      <a href="{{ url_for('dashboard', page='ds-lesson') }}?i={{ completed }}" class="btn" style="margin-top:15px">Continue Lesson</a>
    {% else %}
      <div style="margin-top: 20px; color: var(--accent-pink); padding: 15px; border: 1px dashed var(--accent-pink); border-radius: 8px; background: rgba(255,51,153,0.1);">
        <p>✅ All lessons completed! Time for your final assessment.</p>
        <a href="{{ url_for('dashboard', page='ds-final-quiz') }}" class="btn" style="margin-top: 10px;">Start Final {{ user.level.title() }} Quiz ({{ quiz_total_questions }} Qs)</a>
      </div>
    {% endif %}

  {% endif %}
</div>
{% endblock %}"""

SUBJECTS_CONTENT = r"""{% extends 'DASHBOARD_HTML' %}{% block main_content %}
<div class="card">
  <h2>Data Structures Learning Path</h2>
  <p>Start the quiz to set your level, then watch lessons with chat help.</p>
</div>
<div class="card">
  {% if user.level == 'unassigned' %}
    <a href="{{ url_for('dashboard', page='ds-quiz') }}" class="btn">Start Pre-Assessment Quiz</a>
  {% elif user.quiz_status == 'completed_advance' %}
     <p>Your journey is complete! You are a Data Structures Master.</p>
  {% elif completed < total %}
    <a href="{{ url_for('dashboard', page='ds-lesson') }}?i={{ completed }}" class="btn">Continue Lessons ({{ user.level.title() }})</a>
  {% else %}
    <div style="margin-top: 20px; color: var(--accent-pink); padding: 15px; border: 1px dashed var(--accent-pink); border-radius: 8px; background: rgba(255,51,153,0.1);">
      <p>✅ Lessons completed! Click below to move to the next level's final quiz.</p>
      <a href="{{ url_for('dashboard', page='ds-final-quiz') }}" class="btn">Start Final {{ user.level.title() }} Quiz ({{ quiz_total_questions }} Qs)</a>
    </div>
  {% endif %}
</div>
{% endblock %}"""

QUIZ_CONTENT = r"""{% extends 'DASHBOARD_HTML' %}{% block main_content %}<div class="card">
  <h2>Data Structures Pre-Assessment Quiz (10 Questions)</h2>
  <p class="hint">Your score determines your starting level: **Easy (0-4), Medium (5-7), or Advanced (8-10)**. This quiz is only conducted **one time**.</p>
  <form method="POST"><input type="hidden" name="action" value="submit_pre_quiz">
    <div style="margin-bottom: 15px;"><p style="font-weight: 600;">Q1: Queue characteristic?</p><label style="margin-right: 15px;"><input type="radio" name="q1" value="A" required> FIFO</label> <label style="margin-right: 15px;"><input type="radio" name="q1" value="B"> LIFO</label> <label style="margin-right: 15px;"><input type="radio" name="q1" value="C"> Random Access</label></div>
    <div style="margin-bottom: 15px;"><p style="font-weight: 600;">Q2: Singly linked list operation requiring traversal?</p><label style="margin-right: 15px;"><input type="radio" name="q2" value="A" required> Insert head</label> <label style="margin-right: 15px;"><input type="radio" name="q2" value="B"> Insert tail</label> <label style="margin-right: 15px;"><input type="radio" name="q2" value="C"> Delete head</label></div>
    <div style="margin-bottom: 15px;"><p style="font-weight: 600;">Q3: Recursion is implemented using?</p><label style="margin-right: 15px;"><input type="radio" name="q3" value="A" required> Queue</label> <label style="margin-right: 15px;"><input type="radio" name="q3" value="B"> Array</label> <label style="margin-right: 15px;"><input type="radio" name="q3" value="C"> Stack</label></div>
    <div style="margin-bottom: 15px;"><p style="font-weight: 600;">Q4: Hash table average search?</p><label style="margin-right: 15px;"><input type="radio" name="q4" value="A" required> O(1)</label> <label style="margin-right: 15px;"><input type="radio" name="q4" value="B"> O(log n)</label> <label style="margin-right: 15px;"><input type="radio" name="q4" value="C"> O(n)</label></div>
    <div style="margin-bottom: 15px;"><p style="font-weight: 600;">Q5: BST property?</p><label style="margin-right: 15px;"><input type="radio" name="q5" value="A" required> All nodes have 2 children</label> <label style="margin-right: 15px;"><input type="radio" name="q5" value="B"> left &lt; root &lt; right</label> <label style="margin-right: 15px;"><input type="radio" name="q5" value="C"> Must be complete</label></div>
    <div style="margin-bottom: 15px;"><p style="font-weight: 600;">Q6: Best DS for Dijkstra?</p><label style="margin-right: 15px;"><input type="radio" name="q6" value="A" required> Stack</label> <label style="margin-right: 15px;"><input type="radio" name="q6" value="B"> Hash Map</label> <label style="margin-right: 15px;"><input type="radio" name="q6" value="C"> Priority Queue</label></div>
    <div style="margin-bottom: 15px;"><p style="font-weight: 600;">Q7: Worst-case space of Array?</p><label style="margin-right: 15px;"><input type="radio" name="q7" value="A" required> O(n)</label> <label style="margin-right: 15px;"><input type="radio" name="q7" value="B"> O(1)</label> <label style="margin-right: 15px;"><input type="radio" name="q7" value="C"> O(n log n)</label></div>
    <div style="margin-bottom: 15px;"><p style="font-weight: 600;">Q8: Dynamic memory in C?</p><label style="margin-right: 15px;"><input type="radio" name="q8" value="A" required> Stack</label> <label style="margin-right: 15px;"><input type="radio" name="q8" value="B"> Heap</label> <label style="margin-right: 15px;"><input type="radio" name="q8" value="C"> Global</label></div>
    <div style="margin-bottom: 15px;"><p style="font-weight: 600;">Q9: Max edges undirected with n vertices?</p><label style="margin-right: 15px;"><input type="radio" name="q9" value="A" required> n</label> <label style="margin-right: 15px;"><input type="radio" name="q9" value="B"> n-1</label> <label style="margin-right: 15px;"><input type="radio" name="q9" value="C"> n(n-1)/2</label></div>
    <div style="margin-bottom: 15px;"><p style="font-weight: 600;">Q10: Visiting every node in a tree is?</p><label style="margin-right: 15px;"><input type="radio" name="q10" value="A" required> Traversal</label> <label style="margin-right: 15px;"><input type="radio" name="q10" value="B"> Searching</label> <label style="margin-right: 15px;"><input type="radio" name="q10" value="C"> Sorting</label></div>
    <p><button class="btn" style="margin-top:20px">Submit & Set Level</button></p></form></div>{% endblock %}"""

RESULT_CONTENT = r"""{% extends 'DASHBOARD_HTML' %}{% block main_content %}<div class="card" style="padding: 30px; text-align: center;"><h2 style="color: var(--accent-pink);">✅ Pre-Assessment Completed!</h2><p style="font-size: 1.1em;">Your Score: <b>{{ user.score }}/10</b></p><p style="font-size: 1.2em;">Starting Level: <b style="text-transform: uppercase; color: var(--ok);">{{ user.level }}</b></p><a href="{{ url_for('dashboard', page='ds-lesson') }}" class="btn" style="margin-top: 20px;">Start {{ user.level.title() }} Lessons</a></div>{% endblock %}"""

FINAL_QUIZ_CONTENT = r"""{% extends 'DASHBOARD_HTML' %}{% block main_content %}<div class="card">
    <h2>Final {{ level|title }} Level Assessment ({{ quiz_data.total }} Questions)</h2>
    <p class="hint">Pass mark for promotion is <b>{{ quiz_data.pass_threshold }}</b> correct answers.</p>
    <form method="POST"><input type="hidden" name="action" value="submit_final_quiz">

    {% for q_num, q_data in quiz_data.questions.items() %}
        <div style="margin-bottom: 15px;">
            <p style="font-weight: 600;">{{ q_num|replace("q", "Q") }}: {{ q_data.q }}</p>
            {% for opt in q_data.opts %}
                <label style="margin-right: 20px;"><input type="radio" name="{{ q_num }}" value="{{ opt }}" required> {{ opt }}</label>
            {% endfor %}
        </div>
        {% if loop.index == 10 and quiz_data.total > 10 %}<hr style="margin: 20px 0; border-top: 1px dashed var(--muted);">{% endif %}
    {% endfor %}

    <p><button class="btn" style="margin-top:20px">Submit Final Assessment</button></p>
    </form>
</div>{% endblock %}"""

FINAL_QUIZ_RESULT_CONTENT = r"""{% extends 'DASHBOARD_HTML' %}{% block main_content %}<div class="card" style="padding: 30px;">
    <h2>{% if promoted %}🥳 Promotion Successful!{% else %}❌ Quiz Failed{% endif %}</h2>
    <p style="font-size: 1.1em;">Your Final {{ current_level|title }} Quiz Score: <b>{{ score }}/{{ total_questions }}</b></p>

    {% if promoted %}
        <div style="background: rgba(34, 197, 94, 0.1); padding: 20px; border-radius: 8px; border: 1px solid var(--ok); margin-top: 20px;">
            <p style="font-size: 1.2em; color: var(--ok); font-weight: 600;">Congratulations! You passed and have been moved to the <b>{{ new_level|upper }}</b> level.</p>
            <a href="{{ url_for('dashboard', page='ds-lesson') }}" class="btn" style="background: var(--ok); margin-top: 15px; box-shadow: none;">Start {{ new_level|title }} Lessons</a>
        </div>
    {% else %}
        <div style="background: rgba(220, 38, 38, 0.1); padding: 20px; border-radius: 8px; border: 1px solid var(--warn); margin-top: 20px;">
            <p style="font-size: 1.1em; color: var(--warn); font-weight: 600;">You need a score of <b>{{ pass_threshold }}</b> or higher to advance. Please re-review the {{ current_level|title }} content.</p>
            <a href="{{ url_for('dashboard', page='ds-lesson') }}" class="btn" style="background: var(--warn); margin-top: 15px; box-shadow: none;">Review {{ current_level|title }} Lessons</a>
        </div>
    {% endif %}
</div>{% endblock %}"""

COURSE_COMPLETE_CONTENT = r"""{% extends 'DASHBOARD_HTML' %}{% block main_content %}<div class="card">
    <div style="text-align: center; padding: 40px; background: rgba(0, 255, 255, 0.1); border: 2px solid var(--accent-blue); border-radius: 12px;">
        <h2 style="font-size: 2.5em; color: var(--accent-blue);">🏆 COURSE COMPLETED! 🏆</h2>
        <p style="font-size: 1.2em; margin: 20px 0;">You have successfully mastered the Easy, Medium, and Advanced Data Structures curriculum.</p>
        <p style="font-weight: bold;">Your final score on the Advanced Quiz was: <b>{{ score }}/{{ LEVEL_QUIZ_MAP.advance.total }}</b></p>
        <p style="margin-top: 30px;">Thank thank you for using the AI Tech Tutor!</p>
        <a href="{{ url_for('dashboard', page='scoreboard') }}" class="btn">View Final Scoreboard Rank</a>
      </div>
</div>{% endblock %}"""

LESSON_CONTENT = r"""{% extends 'DASHBOARD_HTML' %}{% block main_content %}
<div class="card" style="display:flex;gap:24px;flex-wrap:wrap;padding: 30px;">
  <div style="flex:3;min-width:320px;max-width:820px;">
    <h2>Data Structures: {{ level|title }} — Lesson {{ index + 1 }} of {{ total_lessons }}</h2>
    <h3 class="hint" style="margin-top:-6px">{{ lesson_title }}</h3>
    <div class="progress" style="margin:10px 0 14px;"><div style="width: {{ lesson_progress_percent }}%"></div></div>
    <p class="hint" style="margin-top:-4px;">Progress: {{ completed_lessons }}/{{ total_lessons }} lessons ({{ lesson_progress_percent }}%)</p>

    <div style="position:relative;width:100%;padding-bottom:56.25%;height:0;border-radius:12px;overflow:hidden;margin:12px 0 18px; box-shadow: 0 4px 10px rgba(0,0,0,.3);">
      <iframe width="100%" height="100%" src="{{ video_url }}" title="Lesson" frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              referrerpolicy="strict-origin-when-cross-origin" allowfullscreen
              style="position:absolute;top:0;left:0"></iframe>
    </div>

    <h3 style="color: var(--accent-blue);">🤖 AI Summary & Key Concept</h3>
    <div class="card" style="padding:16px;background:rgba(0,0,0,0.2);border:1px solid var(--accent-blue); box-shadow: none;">{{ summary | safe }}</div>

    <div class="row" style="margin-top:12px">
      <a href="{{ prev_url }}" class="btn ghost" {% if prev_disabled %}disabled{% endif %}>← Previous</a>
      {% if is_last_lesson %}
        <a href="{{ next_url }}" class="btn" style="background: var(--ok); box-shadow: none;">✅ Finish Level & Start Quiz!</a>
      {% else %}
        <a href="{{ next_url }}" class="btn">Next →</a>
      {% endif %}
    </div>
  </div>

  <div style="flex:1.5;min-width:350px;">
    <div class="card chat">
      <h3 style="margin-bottom: 10px; color: var(--accent-pink);">🤖 AI Doubt Chat</h3>
      <div id="chat-window" style="height:650px;overflow:auto;padding-right: 8px;">
        <div class="bubble ai">Welcome to the AI Doubt Chat! Ask anything about the current lesson.</div>
        <div class="bubble ai">Simulated voice command is now a simple button for web deployment.</div>
      </div>
      <div class="row" style="margin-top:15px">
        <input id="chat-input" class="input" placeholder="Ask a question about the lesson...">
        <button class="btn" onclick="sendChat()" style="padding: 10px 14px;">➤</button>
      </div>
      <button class="btn" style="width:100%;background:#dc2626;margin-top:8px; box-shadow: none;" onclick="simulatedVoiceCommand()">🎙️ Voice Command (Simulated)</button>
    </div>
  </div>
</div>
<script>
const chatWin=document.getElementById('chat-window');
const chatInput=document.getElementById('chat-input');
const lessonLevel="{{ level }}";
const lessonContent="{{ lesson_desc | escape }}";
const chatPath = '{{ url_for("chat_response") }}';

function scrollDown(){ chatWin.scrollTop=chatWin.scrollHeight;}

function addMsg(sender,text){
  const b=document.createElement('div'); b.className='bubble '+(sender==='user'?'user':'ai'); b.innerHTML=text;
  chatWin.appendChild(b); scrollDown();
}

async function fetchChatResponse(question, isVoice = false) {
  chatInput.disabled = true;
  const loader=document.createElement('div');
  loader.id='loading';
  loader.className='bubble ai';
  loader.innerHTML = isVoice ? 'AI processing voice command...' : 'AI typing...';
  chatWin.appendChild(loader);
  scrollDown();

  try {
    const response = await fetch(chatPath, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_question: question,
            level: lessonLevel,
            context: lessonContent
        })
    });

    const L=document.getElementById('loading'); if(L) L.remove();
    chatInput.disabled = false;
    chatInput.focus();

    if (!response.ok) {
        addMsg('ai', '⚠️ Network Error: Could not reach the AI service. Status: ' + response.status);
        return;
    }

    const data = await response.json();
    addMsg('ai', (data && data.response) ? data.response : '⚠️ No valid response received.');

  } catch(error) {
    const L=document.getElementById('loading'); if(L) L.remove();
    chatInput.disabled = false;
    chatInput.focus();
    addMsg('ai','Sorry, a communication error occurred: ' + error.message);
  }
}

function sendChat(){
  const msg=chatInput.value.trim();
  if(!msg) return;
  addMsg('user',msg);
  chatInput.value='';
  fetchChatResponse(msg, false);
}

function simulatedVoiceCommand() {
  const simulatedQuestion = "What is the Big O notation for the key concept in this lesson?";
  addMsg('user', "🎙️ [Simulated Voice Command] " + simulatedQuestion);
  fetchChatResponse(simulatedQuestion, true);
}

// Event listener for the Enter key to send chat
chatInput.addEventListener('keypress', e=>{
  if(e.key==='Enter'){
    e.preventDefault();
    sendChat();
  }
});

scrollDown();
</script>
{% endblock %}"""

SCOREBOARD_CONTENT = r"""{% extends 'DASHBOARD_HTML' %}{% block main_content %}<div class="card"><h2>🏆 Global Data Structures Scoreboard</h2><table style="width:100%;border-collapse:collapse; margin-top: 15px;"><tr><th style="text-align:left;padding:12px;border-bottom:2px solid rgba(255,255,255,0.1)">Rank</th><th style="text-align:left;padding:12px;border-bottom:2px solid rgba(255,255,255,0.1)">Name</th><th style="text-align:left;padding:12px;border-bottom:2px solid rgba(255,255,255,0.1)">Level</th><th style="text-align:left;padding:12px;border-bottom:2px solid rgba(255,255,255,0.1)">Score</th></tr>{% for u in all_users %}<tr {% if u.email==user.email %}style="background:rgba(255,255,255,0.1);font-weight:600"{% endif %}><td style="padding:12px">{% if loop.index==1 %}<span style="color: gold;">🥇</span>{% elif loop.index==2 %}<span style="color: silver;">🥈</span>{% elif loop.index==3 %}<span style="color: #cd7f32;">🥉</span>{% else %}{{ loop.index }}{% endif %}</td><td style="padding:12px">{{ u.name }}{% if u.email==user.email %} (You){% endif %}</td><td style="padding:12px;text-transform:capitalize">{{ u.level }}{% if u.quiz_status == 'completed_advance' %} (Master){% endif %}</td><td style="padding:12px">{{ u.score }}</td></tr>{% endfor %}</table></div>{% endblock %}"""

TEMPLATE_STRINGS = {
    'BASE_HTML': BASE_HTML, 'LOGIN_HTML': LOGIN_HTML, 'SIGNUP_HTML': SIGNUP_HTML,
    'DASHBOARD_HTML': DASHBOARD_HTML, 'HOME_CONTENT': HOME_CONTENT,
    'SUBJECTS_CONTENT': SUBJECTS_CONTENT, 'QUIZ_CONTENT': QUIZ_CONTENT,
    'LESSON_CONTENT': LESSON_CONTENT, 'SCOREBOARD_CONTENT': SCOREBOARD_CONTENT,
    'RESULT_CONTENT': RESULT_CONTENT,
    'FINAL_QUIZ_CONTENT': FINAL_QUIZ_CONTENT,
    'FINAL_QUIZ_RESULT_CONTENT': FINAL_QUIZ_RESULT_CONTENT,
    'COURSE_COMPLETE_CONTENT': COURSE_COMPLETE_CONTENT,
}

def render_template(template_name, **kwargs):
    loader = DictLoader(TEMPLATE_STRINGS)
    env = Environment(loader=loader)
    env.globals.update({'url_for': url_for, 'get_flashed_messages': get_flashed_messages,
                        'LEVEL_QUIZ_MAP': LEVEL_QUIZ_MAP})
    template = env.get_template(template_name)
    return template.render(**kwargs)

# ==============================================================================
# 5. Flask Routes
# ==============================================================================

@app.route('/api/check_email')
def api_check_email():
    """API endpoint for real-time email existence check during signup."""
    email = request.args.get('email','').strip()
    exists = bool(get_user_by_email(email))
    return jsonify({'exists': exists})

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_email' in session:
        return redirect(url_for('dashboard', page='home'))
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = get_user_by_email(email)

        if user and check_password_hash(user['password'], password):
            session['user_email'] = email
            return redirect(url_for('dashboard', page='home'))
        else:
            error = "Invalid email or password."
    return render_template('LOGIN_HTML', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_email' in session:
        return redirect(url_for('dashboard', page='home'))
    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not re.fullmatch(EMAIL_REGEX, email):
              error = "Invalid email format."
        elif len(password) < PASSWORD_MIN_LENGTH or not (re.search(r'[A-Z]', password) and re.search(r'[a-z]', password) and re.search(r'\d', password)):
            error = "Password must be min 8 chars with upper, lower & digit."
        else:
            hashed_password = generate_password_hash(password)

            if add_new_user(email, hashed_password, name):
                session['user_email'] = email
                return redirect(url_for('dashboard', page='home'))
            else:
                error = "This email address is already registered."

    return render_template('SIGNUP_HTML', error=error)

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('login'))

@app.route('/dashboard/<page>', methods=['GET', 'POST'])
def dashboard(page):
    if 'user_email' not in session:
        return redirect(url_for('login'))

    user_email = session['user_email']
    user_data = get_user_by_email(user_email)

    if not user_data:
        session.pop('user_email', None)
        return redirect(url_for('login'))

    current_level = user_data.get('level', 'unassigned')
    quiz_status = user_data.get('quiz_status', 'pending_pre')

    total_lessons = len(LESSONS.get(current_level, []))
    completed_lessons_index = get_progress(user_email, current_level) if current_level != 'unassigned' else 0
    completed_lessons_count = completed_lessons_index
    total_lessons_for_progress = max(1, total_lessons)
    progress_percent = round((completed_lessons_count / total_lessons_for_progress) * 100)

    current_quiz_map = LEVEL_QUIZ_MAP.get(current_level, {})
    quiz_total_questions = current_quiz_map.get('total', 20)

    # --- Flow Control ---
    if quiz_status == 'completed_advance' and page not in ['course-complete', 'scoreboard']:
      return redirect(url_for('dashboard', page='course-complete'))

    is_quiz_done = current_level != 'unassigned'
    if page == 'ds-quiz' and is_quiz_done:
      if quiz_status == 'pending_pre': return redirect(url_for('dashboard', page='ds-result'))
      else: return redirect(url_for('dashboard', page='home'))

    if current_level != 'unassigned':
      if completed_lessons_index < total_lessons:
          if page == 'ds-final-quiz' or page == 'ds-final-result':
              return redirect(url_for('dashboard', page='ds-lesson', i=completed_lessons_index))
      else:
          if page not in ['ds-final-quiz', 'ds-final-result', 'course-complete', 'scoreboard']:
              return redirect(url_for('dashboard', page='ds-final-quiz'))

    # --- POST Handling (Quizzes) ---
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'submit_pre_quiz':
            if quiz_status != 'pending_pre': return redirect(url_for('dashboard', page='home'))
            score = 0
            for i in range(1, 11):
                if request.form.get(f'q{i}') == QUIZ_ANSWERS[f'q{i}']: score += 1

            if score >= 8: new_level = 'advance'
            elif score >= 5: new_level = 'medium'
            else: new_level = 'easy'

            update_user_quiz_result(user_email, new_level, score, 'completed_pre')
            return redirect(url_for('dashboard', page='ds-result'))

        elif action == 'submit_final_quiz':
            quiz_questions_map = LEVEL_QUIZ_MAP.get(current_level)
            if not quiz_questions_map: return redirect(url_for('dashboard', page='home'))
            correct_answers = quiz_questions_map['correct_answers']
            total_questions = quiz_questions_map['total']
            pass_threshold = quiz_questions_map['pass_threshold']

            score = 0
            for q_num, correct_ans in correct_answers.items():
                if request.form.get(q_num) == correct_ans: score += 1

            promoted = score >= pass_threshold
            next_level_map = {'easy': 'medium', 'medium': 'advance', 'advance': 'completed_advance'}
            new_level = current_level
            new_status = f'completed_{current_level}'

            if promoted:
                if current_level == 'advance':
                    new_status = 'completed_advance'
                    update_user_quiz_result(user_email, current_level, score, new_status)
                    return redirect(url_for('dashboard', page='course-complete', score=score))
                else:
                    new_level = next_level_map.get(current_level)
                    update_user_quiz_result(user_email, new_level, score, new_status)
            else:
                update_user_quiz_result(user_email, current_level, score, new_status)
                set_progress(user_email, current_level, 0)

            return redirect(url_for('dashboard', page='ds-final-result', score=score, promoted=promoted,
                                    new_level=new_level, current_level=current_level, total_questions=total_questions))

    user_data = get_user_by_email(user_email)

    # --- Route Page Rendering ---
    if page == 'home':
        return render_template('HOME_CONTENT', page=page, user=user_data, level=current_level,
                               completed=completed_lessons_count, total=total_lessons_for_progress,
                               progress_percent=progress_percent, quiz_status=quiz_status,
                               quiz_total_questions=quiz_total_questions)
    elif page == 'subjects':
        return render_template('SUBJECTS_CONTENT', page=page, user=user_data, level=current_level,
                               completed=completed_lessons_count, total=total_lessons_for_progress,
                               quiz_total_questions=quiz_total_questions)
    elif page == 'scoreboard':
        all_users = get_all_users_by_score()
        return render_template('SCOREBOARD_CONTENT', page=page, user=user_data, all_users=all_users)
    elif page == 'ds-quiz':
        return render_template('QUIZ_CONTENT', page=page, user=user_data, level=current_level)
    elif page == 'ds-result':
        return render_template('RESULT_CONTENT', page=page, user=user_data, level=current_level)
    elif page == 'ds-final-quiz':
        quiz_data = LEVEL_QUIZ_MAP.get(current_level)
        return render_template('FINAL_QUIZ_CONTENT', page=page, user=user_data, level=current_level, quiz_data=quiz_data)
    elif page == 'ds-final-result':
        score = request.args.get('score', type=int, default=0)
        promoted = request.args.get('promoted', default='False') == 'True'
        new_level = request.args.get('new_level')
        current_level_param = request.args.get('current_level')
        total_questions = request.args.get('total_questions', type=int, default=20)
        pass_threshold = LEVEL_QUIZ_MAP.get(current_level_param, {}).get('pass_threshold', 8)

        return render_template('FINAL_QUIZ_RESULT_CONTENT', page=page, user=user_data, score=score, promoted=promoted,
                               new_level=new_level, current_level=current_level_param, total_questions=total_questions,
                               pass_threshold=pass_threshold)

    elif page == 'course-complete':
        score = request.args.get('score', type=int, default=user_data.get('score', 0))
        return render_template('COURSE_COMPLETE_CONTENT', page=page, user=user_data, score=score)

    elif page == 'ds-lesson':
        lessons = LESSONS.get(current_level, [])
        if not lessons: return redirect(url_for('dashboard', page='home'))

        q_i = request.args.get('i', type=int)
        cur_i = get_progress(user_email, current_level)

        if cur_i >= total_lessons: return redirect(url_for('dashboard', page='ds-final-quiz'))

        if q_i is not None:
             new_i = max(0, min(total_lessons, q_i))
             if new_i > cur_i: set_progress(user_email, current_level, new_i); cur_i = new_i
             else: cur_i = new_i

        if cur_i == total_lessons: return redirect(url_for('dashboard', page='ds-final-quiz'))

        completed_lessons_index = get_progress(user_email, current_level)
        lesson = lessons[completed_lessons_index]

        prev_disabled = completed_lessons_index <= 0
        is_last_lesson = completed_lessons_index == total_lessons - 1

        def make_url(i): return url_for('dashboard', page='ds-lesson') + '?' + urlencode({'i': i})
        prev_url = '#' if prev_disabled else make_url(completed_lessons_index - 1)
        next_url = make_url(completed_lessons_index + 1)

        completed_lessons_count_display = completed_lessons_index + 1
        lesson_progress_percent = round((completed_lessons_count_display / total_lessons) * 100)

        summary = generate_video_summary(current_level, lesson['desc'])

        return render_template(
            'LESSON_CONTENT', page=page, user=user_data, level=current_level,
            index=completed_lessons_index, total_lessons=total_lessons, lesson_title=lesson['title'],
            video_url=lesson['url'], lesson_desc=lesson['desc'], summary=summary,
            prev_url=prev_url, next_url=next_url, prev_disabled=prev_disabled,
            next_disabled=False,
            completed_lessons=completed_lessons_count_display,
            lesson_progress_percent=lesson_progress_percent,
            is_last_lesson=is_last_lesson
        )

    return redirect(url_for('dashboard', page='home'))

# ==============================================================================
# 6. Gemini Chat Endpoint 💬
# ==============================================================================

@app.route('/chat_response', methods=['POST'])
def chat_response():
    if 'user_email' not in session: return jsonify({'response': 'Authentication required.'}), 401
    data = request.get_json()
    user_question = data.get('user_question', '').strip()
    level = data.get('level', 'easy')
    lesson_context = data.get('context', 'Linked Lists and Arrays.')

    if not user_question: return jsonify({'response': 'Please ask a question.'})

    system_prompt = (
        f"You are the AI Tech Tutor, specialized in Data Structures at the {level.title()} level. "
        f"The current lesson topic is: '{lesson_context}'. "
        "Your goal is to answer the user's question concisely, clearly, and always within the context of Data Structures. "
        "Provide detailed and in-depth explanations. Use **bold** formatting for key terms."
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[{"role": "user", "parts": [{"text": system_prompt}, {"text": f"User's question: {user_question}"}]}]
        )
        return jsonify({'response': response.text})

    except APIError:
        return jsonify({'response': 'Sorry, the AI service is currently unavailable.'})
    except Exception:
        return jsonify({'response': 'An unknown error occurred during chat processing.'})

# ==============================================================================
# 7. Server Run Block (Local Testing Only) 🖥️
# ==============================================================================

if __name__ == '__main__':
    # This block is used only when running the file directly (e.g., python app.py)
    # in your local development environment.
    print("Running Flask app locally for testing...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
