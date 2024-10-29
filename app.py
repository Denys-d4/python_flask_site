import os
import json
import jwt
import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from functools import wraps

app = Flask(__name__)

# Secret key for JWT (make sure to keep it secret in a real application)
app.config['SECRET_KEY'] = 'your_secret_key'

# Path to JSON files
USERS_FILE = './data/users.json'
CHAT_FILE = './data/chat.json'

# Utility function to load or create JSON data
def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            return json.load(file)
    return {}

def save_json(filepath, data):
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

# JWT Token required decorator
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('login'))

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Load or create user data
        users = load_json(USERS_FILE)

        if email in users:
            return "User already exists. Try a different email."

        # Save user data
        users[email] = {
            "name": name,
            "password": password
        }
        save_json(USERS_FILE, users)

        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        users = load_json(USERS_FILE)

        if email in users and users[email]['password'] == password:
            # Create JWT token
            token = jwt.encode({
                'user': email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            response = make_response(redirect(url_for('profile')))
            response.set_cookie('token', token)
            return response

        return "Invalid credentials. Please try again."

    return render_template('login.html')

@app.route('/profile')
@token_required
def profile():
    token = request.cookies.get('token')
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    user_email = data['user']
    
    users = load_json(USERS_FILE)
    user_info = users.get(user_email, {})
    user_info['email'] = user_email  # Include email in user_info for display
    
    return render_template('profile.html', user=user_info)

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('token', '', expires=0)  # Remove the token cookie
    return response


@app.route('/chat', methods=['GET', 'POST'])
#@token_required
def chat():
    # Load chat messages
    messages = load_json(CHAT_FILE)

    if request.method == 'POST':

        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('login'))
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return redirect(url_for('login'))

        token = request.cookies.get('token')
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_email = data['user']
        
        message = request.form.get('message')

        # Add new message
        if message:
            messages.append({
                "user": user_email,
                "message": message,
                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            save_json(CHAT_FILE, messages)

        return redirect(url_for('chat'))

    return render_template('chat.html', messages=messages)

if __name__ == '__main__':
    # Ensure data folder exists
    if not os.path.exists('./data'):
        os.makedirs('./data')

    # Initialize JSON files if they do not exist
    if not os.path.exists(USERS_FILE):
        save_json(USERS_FILE, {})
    if not os.path.exists(CHAT_FILE):
        save_json(CHAT_FILE, [])

    app.run(debug=True)
