from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import random
import datetime
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Application initialization
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set secret key for session management

# Initialize data storage (in a real app, use a database)
# In-memory storage for demonstration
USERS_DB = {}
QUESTIONS_DB = [
    {
        "id": 1,
        "question": "What is the capital of France?",
        "options": ["London", "Berlin", "Paris", "Madrid"],
        "correct_answer": "Paris"
    },
    {
        "id": 2,
        "question": "Which planet is known as the Red Planet?",
        "options": ["Earth", "Mars", "Jupiter", "Venus"],
        "correct_answer": "Mars"
    },
    {
        "id": 3,
        "question": "What is the largest mammal?",
        "options": ["Elephant", "Blue Whale", "Giraffe", "Hippopotamus"],
        "correct_answer": "Blue Whale"
    },
    {
        "id": 4,
        "question": "Which language runs in a web browser?",
        "options": ["Java", "C", "Python", "JavaScript"],
        "correct_answer": "JavaScript"
    },
    {
        "id": 5,
        "question": "What is the chemical symbol for gold?",
        "options": ["Go", "Ag", "Au", "Gl"],
        "correct_answer": "Au"
    }
]

QUIZ_RESULTS = {}  # Store user quiz results

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS_DB:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        # Create user
        USERS_DB[username] = {
            'password_hash': generate_password_hash(password),
            'quiz_history': []
        }
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username not in USERS_DB or not check_password_hash(USERS_DB[username]['password_hash'], password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        session['username'] = username
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    quiz_history = USERS_DB[username]['quiz_history']
    return render_template('dashboard.html', username=username, quiz_history=quiz_history)

@app.route('/start_quiz', methods=['GET', 'POST'])
@login_required
def start_quiz():
    if request.method == 'POST':
        quiz_duration = int(request.form['quiz_duration'])  # Duration in minutes
        num_questions = int(request.form['num_questions'])
        
        # Ensure we don't request more questions than available
        num_questions = min(num_questions, len(QUESTIONS_DB))
        
        # Select random questions and shuffle options
        selected_questions = random.sample(QUESTIONS_DB, num_questions)
        for question in selected_questions:
            # Create a copy of options and shuffle them
            options = question['options'].copy()
            random.shuffle(options)
            question['shuffled_options'] = options
        
        # Store quiz in session
        session['quiz'] = {
            'questions': selected_questions,
            'start_time': datetime.datetime.now().isoformat(),
            'duration': quiz_duration,
            'num_questions': num_questions
        }
        
        return redirect(url_for('quiz'))
    
    return render_template('start_quiz.html')

@app.route('/quiz')
@login_required
def quiz():
    if 'quiz' not in session:
        flash('Please start a new quiz', 'warning')
        return redirect(url_for('start_quiz'))
    
    quiz_data = session['quiz']
    questions = quiz_data['questions']
    start_time = datetime.datetime.fromisoformat(quiz_data['start_time'])
    duration_minutes = quiz_data['duration']
    
    # Calculate end time and remaining time
    end_time = start_time + datetime.timedelta(minutes=duration_minutes)
    remaining_seconds = int((end_time - datetime.datetime.now()).total_seconds())
    
    # If time is up, redirect to results
    if remaining_seconds <= 0:
        flash('Time is up! Quiz automatically submitted.', 'info')
        return redirect(url_for('submit_quiz'))
    
    return render_template('quiz.html', 
                          questions=questions, 
                          remaining_seconds=remaining_seconds,
                          quiz_duration_minutes=duration_minutes)

@app.route('/submit_quiz', methods=['POST', 'GET'])
@login_required
def submit_quiz():
    if 'quiz' not in session:
        flash('No quiz in progress', 'warning')
        return redirect(url_for('start_quiz'))
    
    # Calculate score if POST request (form submitted)
    if request.method == 'POST':
        quiz_data = session['quiz']
        questions = quiz_data['questions']
        
        # Calculate score
        correct_answers = 0
        user_answers = {}
        
        for question in questions:
            q_id = str(question['id'])
            if q_id in request.form:
                user_answer = request.form[q_id]
                user_answers[q_id] = user_answer
                if user_answer == question['correct_answer']:
                    correct_answers += 1
        
        # Calculate score as percentage
        score = (correct_answers / len(questions)) * 100 if questions else 0
        
        # Store quiz result
        quiz_result = {
            'timestamp': datetime.datetime.now().isoformat(),
            'score': score,
            'correct_answers': correct_answers,
            'total_questions': len(questions),
            'user_answers': user_answers
        }
        
        # Add to user history
        username = session['username']
        USERS_DB[username]['quiz_history'].append(quiz_result)
        
        # Store in session for immediate access in results page
        session['last_quiz_result'] = quiz_result
        
        # Clear the quiz from session
        session.pop('quiz', None)
        
        return redirect(url_for('quiz_results'))
    
    # Handle GET request (e.g., time expired or manual navigation)
    return redirect(url_for('quiz_results'))

@app.route('/quiz_results')
@login_required
def quiz_results():
    if 'last_quiz_result' not in session:
        flash('No quiz results available', 'warning')
        return redirect(url_for('dashboard'))
    
    result = session['last_quiz_result']
    return render_template('quiz_results.html', result=result)

@app.route('/analytics')
@login_required
def analytics():
    username = session['username']
    quiz_history = USERS_DB[username]['quiz_history']
    
    # Prepare data for charts
    scores = [quiz['score'] for quiz in quiz_history]
    dates = [quiz['timestamp'].split('T')[0] for quiz in quiz_history]  # Just use the date portion
    
    # Calculate statistics
    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0
    
    return render_template('analytics.html', 
                          quiz_history=quiz_history,
                          scores=scores,
                          dates=dates,
                          avg_score=avg_score,
                          max_score=max_score,
                          min_score=min_score)

@app.route('/api/quiz_history')
@login_required
def api_quiz_history():
    username = session['username']
    quiz_history = USERS_DB[username]['quiz_history']
    return jsonify(quiz_history)

if __name__ == '__main__':
    app.run(debug=True)