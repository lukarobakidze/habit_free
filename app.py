# habit_free/app.py

import os
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
import hashlib
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/habit_free.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Habit Free startup')

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Determine base directory and set up SQLite database URI
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'habits.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)  # Store hashed password
    email = db.Column(db.String(120), unique=True, nullable=True)  # Add email field
    habits = db.relationship('Habit', backref='user', lazy=True)
    messages = db.relationship('Message', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    start_datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Habit {self.name} (ID: {self.id})>'

    def to_dict(self):
        # ensure the datetime is timezone-aware and in UTC
        start_time = self.start_datetime
        if start_time.tzinfo is None:
            start_time = pytz.utc.localize(start_time)
        return {
            'id': self.id,
            'name': self.name,
            'start_datetime': start_time.isoformat()  
            }

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    send_date = db.Column(db.String(10), nullable=False)
    is_masked = db.Column(db.Boolean, default=True)  # new field for masking state

    def __repr__(self):
        return f'<Message ID: {self.id} for {self.send_date}>'

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'send_date': self.send_date,
            'is_masked': self.is_masked
        }

# helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_and_send_messages():
    """Check for messages that need to be displayed today."""
    try:
        today = datetime.now(timezone.utc).date()
        today_str = today.strftime('%Y-%m-%d')
        
        # get all messages scheduled for today
        messages = Message.query.filter_by(send_date=today_str).all()
        
        for message in messages:
            user = User.query.get(message.user_id)
            if user:
                print(f"Message for user {user.username}: {message.message}")
                
                # optionally delete the message after displaying
                db.session.delete(message)
        
        db.session.commit()
        print(f"Checked messages for {today_str}")
    except Exception as e:
        print(f"Error checking messages: {e}")
        db.session.rollback()

# route handlers
@app.route('/')
def home():
    return "Welcome to Habit Free API !"

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.form
        username = data.get('username')
        password = data.get('password')
        
        app.logger.info(f'Registration attempt for user: {username}')
        
        if not username or not password:
            app.logger.warning('Missing username or password in registration')
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        if not (3 <= len(username) <= 15) or not username.isalnum():
            app.logger.warning(f'Invalid username format: {username}')
            return jsonify({'success': False, 'message': 'Invalid username format'}), 400
        
        if len(password) < 4:
            app.logger.warning('Password too short in registration')
            return jsonify({'success': False, 'message': 'Password too short'}), 400
        
        hashed_password = hash_password(password)
        
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        app.logger.info(f'Successfully registered user: {username}')
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user_id': new_user.id,
            'session_cookie': 'dummy_session'
        })
    except Exception as e:
        app.logger.error(f'Registration error: {str(e)}')
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.form
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Please enter both username and password'}), 400
    
    try:
        # first check if user exists
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({
                'success': False, 
                'message': f'No account found with username "{username}". Please check your spelling or register a new account.'
            }), 401
        
        # then check password
        hashed_password = hash_password(password)
        if user.password != hashed_password:
            return jsonify({
                'success': False, 
                'message': 'Incorrect password. Please try again.'
            }), 401
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user_id': user.id,
            'session_cookie': 'dummy_session'  # in a real app, generate proper session
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get_habits', methods=['GET'])
def get_habits():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required'}), 400
    
    try:
        habits = Habit.query.filter_by(user_id=user_id).all()
        return jsonify({
            'success': True,
            'habits': [habit.to_dict() for habit in habits]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/add', methods=['POST'])
def add_habit():
    data = request.form
    user_id = data.get('user_id')
    name = data.get('name')
    
    if not user_id or not name:
        return jsonify({'success': False, 'message': 'User ID and habit name required'}), 400
    
    try:
        new_habit = Habit(user_id=user_id, name=name)
        db.session.add(new_habit)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Habit added successfully',
            'habit': new_habit.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete/<int:habit_id>', methods=['DELETE'])
def delete_habit(habit_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required'}), 400
    
    try:
        habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first()
        if habit:
            db.session.delete(habit)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Habit deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Habit not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get_messages', methods=['GET'])
def get_messages():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required'}), 400
    
    try:
        messages = Message.query.filter_by(user_id=user_id).all()
        return jsonify({
            'success': True,
            'messages': [message.to_dict() for message in messages]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/inbox', methods=['POST'])
def save_message():
    data = request.form
    user_id = data.get('user_id')
    message = data.get('message')
    date = data.get('date')
    
    if not all([user_id, message, date]):
        return jsonify({'success': False, 'message': 'All fields required'}), 400
    
    try:
        new_message = Message(user_id=user_id, message=message, send_date=date)
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message saved successfully',
            'message_data': new_message.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete_message/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required'}), 400
    
    try:
        message = Message.query.filter_by(id=message_id, user_id=user_id).first()
        if message:
            db.session.delete(message)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Message deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Message not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/toggle_message_mask/<int:message_id>', methods=['POST'])
def toggle_message_mask(message_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required'}), 400
    
    try:
        message = Message.query.filter_by(id=message_id, user_id=user_id).first()
        if message:
            message.is_masked = not message.is_masked
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Message mask toggled successfully',
                'message_data': message.to_dict()
            })
        else:
            return jsonify({'success': False, 'message': 'Message not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# schedule the message checker to run daily at midnight
scheduler.add_job(
    check_and_send_messages,
    'cron',
    hour=0,
    minute=0,
    timezone=pytz.UTC
)

# initialize the app and run first check
def init_app(app):
    with app.app_context():
        db.create_all()
        check_and_send_messages()

@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'404 Error: {error}')
    return jsonify({'success': False, 'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'500 Error: {error}')
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.error(f'Unhandled Exception: {error}')
    return jsonify({'success': False, 'message': str(error)}), 500

#  main Execution
if __name__ == "__main__":
    # initialize the app
    with app.app_context():
        # create database tables if they don't exist
        db.create_all()
        app.logger.info('Database initialized')
        
        # run first message check
        check_and_send_messages()
    
    # run the flask app
    print("Starting Flask server on http://0.0.0.0:5002")
    app.run(debug=True, host='0.0.0.0', port=5002, use_reloader=False)