from werkzeug.security import generate_password_hash, check_password_hash

# --- Configuration Constants ---
PASSWORD_MIN_LENGTH = 8
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
MODEL = 'gemini-2.5-flash'

# --- Quiz Data ---
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

# --- HTML Templates (using raw strings for embedding) ---
# NOTE: In a professional project, these would be separate files in a `templates/` folder.
# We keep them here as raw strings per the original code to preserve the Jinja2 DictLoader approach.
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

    // Initial calls
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
