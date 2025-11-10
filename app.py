import os
import sys
import re
from urllib.parse import urlencode
from flask import Flask, request, redirect, url_for, session, get_flashed_messages, jsonify
from jinja2 import DictLoader, Environment
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai
from google.genai.errors import APIError

# Import local modules
from db_manager import (
    get_user_by_email, add_new_user, update_user_quiz_result, get_user_quiz_status,
    get_all_users_by_score, get_progress, set_progress
)
from data_config import (
    LESSONS, QUIZ_ANSWERS, LEVEL_QUIZ_MAP, TEMPLATE_STRINGS,
    EMAIL_REGEX, PASSWORD_MIN_LENGTH, MODEL
)

# Initialize Flask App
app = Flask(__name__)
# IMPORTANT: In a real deployment, set a strong SECRET_KEY using os.environ
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key_change_me')

# Initialize Gemini Client
try:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        client = genai.Client(api_key=GEMINI_API_KEY)
    else:
        client = None
        print("⚠️ WARNING: GEMINI_API_KEY not set in environment. AI features will be disabled.")
except Exception as e:
    client = None
    print(f"❌ Gemini client initialization failed: {e}. AI features disabled.")


# --- Template Rendering Helper ---
def render_template(template_name, **kwargs):
    loader = DictLoader(TEMPLATE_STRINGS)
    env = Environment(loader=loader)
    env.globals.update({'url_for': url_for, 'get_flashed_messages': get_flashed_messages,
                        'LEVEL_QUIZ_MAP': LEVEL_QUIZ_MAP})
    template = env.get_template(template_name)
    return template.render(**kwargs)

# --- Gemini AI Helper ---
def generate_video_summary(level, desc):
    if not client: return "AI features are disabled. Missing API key."
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

        # 1. Pre-Assessment Quiz (10 Questions)
        if action == 'submit_pre_quiz':
            if quiz_status != 'pending_pre': return redirect(url_for('dashboard', page='home'))

            score = 0
            for i in range(1, 11):
                if request.form.get(f'q{i}') == QUIZ_ANSWERS[f'q{i}']:
                    score += 1

            if score >= 8: new_level = 'advance'
            elif score >= 5: new_level = 'medium'
            else: new_level = 'easy'

            update_user_quiz_result(user_email, new_level, score, 'completed_pre')
            return redirect(url_for('dashboard', page='ds-result'))

        # 2. Final Level Quiz (Dynamically graded)
        elif action == 'submit_final_quiz':
            quiz_questions_map = LEVEL_QUIZ_MAP.get(current_level)
            if not quiz_questions_map: return redirect(url_for('dashboard', page='home'))

            correct_answers = quiz_questions_map['correct_answers']
            total_questions = quiz_questions_map['total']
            pass_threshold = quiz_questions_map['pass_threshold']

            score = 0
            for q_num, correct_ans in correct_answers.items():
                if request.form.get(q_num) == correct_ans:
                    score += 1

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
                set_progress(user_email, current_level, 0) # Force review start

            return redirect(url_for('dashboard', page='ds-final-result', score=score, promoted=promoted,
                                     new_level=new_level, current_level=current_level, total_questions=total_questions))

    user_data = get_user_by_email(user_email)

    # --- Route Page Rendering ---
    if page == 'home':
        return render_template('HOME_CONTENT', page=page, user=user_data, level=current_level,
                               completed=completed_lessons_count, total=total_lessons_for_progress,
                               progress_percent=progress_percent, quiz_status=quiz_status,
                               quiz_total_questions=quiz_total_questions)
    # ... (other pages logic)
    elif page == 'subjects':
        return render_template('SUBJECTS_CONTENT', page=page, user=user_data, level=current_level,
                               completed=completed_lessons_count, total=total_lessons_for_progress,
                               quiz_total_questions=quiz_total_questions)
    elif page == 'scoreboard':
        all_users = get_all_users_by_score()
        return render_template('SCOREBOARD_CONTENT', page=page, user=user_data, all_users=all_users)
    elif page == 'ds-quiz':
        if quiz_status == 'pending_pre': return render_template('QUIZ_CONTENT', page=page, user=user_data, level=current_level)
        else: return redirect(url_for('dashboard', page='home'))
    elif page == 'ds-result':
        if current_level == 'unassigned': return redirect(url_for('dashboard', page='home'))
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
        if quiz_status != 'completed_advance': return redirect(url_for('dashboard', page='home'))
        score = request.args.get('score', type=int, default=user_data.get('score', 0))
        return render_template('COURSE_COMPLETE_CONTENT', page=page, user=user_data, score=score)

    elif page == 'ds-lesson':
        lessons = LESSONS.get(current_level, [])
        if not lessons: return redirect(url_for('dashboard', page='home'))

        q_i = request.args.get('i', type=int)
        cur_i = get_progress(user_email, current_level)

        if cur_i >= total_lessons:
             return redirect(url_for('dashboard', page='ds-final-quiz'))

        if q_i is not None:
             new_i = max(0, min(total_lessons, q_i))
             if new_i > cur_i:
                 set_progress(user_email, current_level, new_i)
                 cur_i = new_i
             else:
                 cur_i = new_i

        if cur_i == total_lessons:
              return redirect(url_for('dashboard', page='ds-final-quiz'))

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
    if not client: return jsonify({'response': 'AI Chat is currently unavailable due to missing API key.'})

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
