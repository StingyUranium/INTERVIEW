from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify, render_template
from auth_db import create_user, verify_user
import os
from livekit import api
from dotenv import load_dotenv
load_dotenv('.env.local')

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a random secret key

# Simple HTML template with Jinja2, includes both signup and login forms with messages
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Signup/Login</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .container { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); width: 320px; }
    h2 { text-align: center; margin-bottom: 1rem; }
    input[type="text"], input[type="password"] { width: 100%; padding: 0.5rem; margin-bottom: 1rem; border-radius: 4px; border: 1px solid #ccc; box-sizing: border-box; }
    button { width: 100%; padding: 0.5rem; background-color: #007bff; border: none; color: white; font-size: 1rem; border-radius: 4px; cursor: pointer; }
    button:hover { background-color: #0056b3; }
    .message { margin: 1rem 0; padding: 0.5rem; border-radius: 4px; }
    .success { background-color: #d4edda; color: #155724; }
    .error { background-color: #f8d7da; color: #721c24; }
    .toggle-link { text-align: center; margin-top: 1rem; }
    .toggle-link a { color: #007bff; text-decoration: none; cursor: pointer; }
    .toggle-link a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="container">
    {% if mode == 'signup' %}
      <h2>Signup</h2>
      {% if message %}
        <div class="message {{ 'success' if success else 'error' }}">{{ message }}</div>
      {% endif %}
      <form method="POST" action="{{ url_for('signup') }}">
        <input type="text" name="username" placeholder="Username" required />
        <input type="password" name="password" placeholder="Password" required />
        <button type="submit">Sign Up</button>
      </form>
      <div class="toggle-link">
        Already have an account? <a href="{{ url_for('login') }}">Login</a>
      </div>
    {% else %}
      <h2>Login</h2>
      {% if message %}
        <div class="message {{ 'success' if success else 'error' }}">{{ message }}</div>
      {% endif %}
      <form method="POST" action="{{ url_for('login') }}">
        <input type="text" name="username" placeholder="Username" required />
        <input type="password" name="password" placeholder="Password" required />
        <button type="submit">Log In</button>
      </form>
      <div class="toggle-link">
        Don't have an account? <a href="{{ url_for('signup') }}">Sign up</a>
      </div>
    {% endif %}
  </div>
</body>
</html>
"""

# --- Routes ---

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = ''
    success = False
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if create_user(username, password):
            message = "Signup successful! You can now log in."
            success = True
        else:
            message = "Username already exists. Try another."
    return render_template_string(HTML_TEMPLATE, mode='signup', message=message, success=success)

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    success = False
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if verify_user(username, password):
            message = f"Welcome back, {username}!"
            success = True
            return redirect(url_for('interview', username=username))
        else:
            message = "Invalid username or password."
    return render_template_string(HTML_TEMPLATE, mode='login', message=message, success=success)

@app.route('/interview')
def interview():
    username = request.args.get('username')
    if not username:
        return redirect(url_for('login'))
    
    livekit_url = os.environ.get('LIVEKIT_URL')
    if not livekit_url:
        return jsonify({'error': 'LIVEKIT_URL not set in .env.local'}), 500

    return render_template('index.html', username=username, livekit_url=livekit_url)

@app.route('/token', methods=['POST'])
def get_token():
    data = request.json
    identity = data.get('identity')
    room = data.get('room', 'interview-room')

    api_key = os.environ.get('LIVEKIT_API_KEY')
    api_secret = os.environ.get('LIVEKIT_API_SECRET')

    if not api_key or not api_secret:
        return jsonify({'error': 'Server configuration missing'}), 500

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_grants(
            api.VideoGrants(
                room=room,
                room_join=True,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
    )
    jwt = token.to_jwt()
    return jsonify({'token': jwt})


@app.route('/frontend')
def frontend():
    return render_template('frontend.html')


if __name__ == "__main__":
    app.run(debug=True)
