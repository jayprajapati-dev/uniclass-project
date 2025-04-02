from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

def get_db():
    db = sqlite3.connect('uniclass.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_admin BOOLEAN DEFAULT 0
            )
        ''')
        db.commit()

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.is_admin = bool(user_data['is_admin'])
        self.created_at = user_data['created_at']

    @staticmethod
    def get(user_id):
        db = get_db()
        user_data = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        db.close()
        if user_data is None:
            return None
        return User(dict(user_data))

    @staticmethod
    def get_by_username(username):
        db = get_db()
        user_data = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        db.close()
        if user_data is None:
            return None
        return User(dict(user_data))

    @staticmethod
    def create(username, email, password):
        db = get_db()
        try:
            hashed_password = generate_password_hash(password)
            db.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed_password)
            )
            db.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            db.close()

    def check_password(self, password):
        db = get_db()
        stored_password = db.execute(
            'SELECT password FROM users WHERE id = ?', (self.id,)
        ).fetchone()['password']
        db.close()
        return check_password_hash(stored_password, password)
