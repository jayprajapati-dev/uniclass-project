from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

def create_app():
    # Create a minimal Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return app

def setup_database():
    try:
        # Remove existing database file
        if os.path.exists('users.db'):
            os.remove('users.db')
            print("Removed existing database file.")
        
        # Create fresh Flask app and database
        app = create_app()
        db = SQLAlchemy(app)
        
        # Define User model
        class User(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(64), unique=True, nullable=False)
            email = db.Column(db.String(120), unique=True, nullable=False)
            password_hash = db.Column(db.String(128))
            name = db.Column(db.String(100))
            role = db.Column(db.String(20), default='student')
            is_admin = db.Column(db.Boolean, default=False)
            is_approved = db.Column(db.Boolean, default=False)
            department = db.Column(db.String(100))
            year = db.Column(db.String(10))
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Create all tables
        with app.app_context():
            db.create_all()
            print("Created database tables.")
            
            # Create admin user
            admin = User(
                username='admin',
                name='Admin User',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                is_admin=True,
                is_approved=True,
                department='Administration',
                year='2024'
            )
            
            # Add admin to database
            db.session.add(admin)
            db.session.commit()
            print("Created admin user:")
            print("Email: admin@example.com")
            print("Password: admin123")
            
            print("\nDatabase setup completed successfully!")
            
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        if 'db' in locals():
            db.session.rollback()

if __name__ == '__main__':
    setup_database() 