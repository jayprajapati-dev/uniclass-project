from flask import Flask, send_from_directory, render_template, request, redirect, url_for, flash, jsonify
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail
from models import User, AdminRole, UserRole, Timetable, TimeSlot, Subject, TimetableEntry, Classroom
from extensions import db, login_manager, socketio
from routes.admin import admin_bp as admin_bp
from routes.auth import auth_bp as auth_bp
from routes.classroom import classroom_bp as classroom_bp
from routes.assignments import assignments_bp
from routes.lost_found import lost_found_bp
from routes.materials import materials_bp
from routes.student import student_bp
from routes.teacher import teacher_bp
from routes.timetable import timetable_bp as timetable_bp
from routes.main import main_bp
from routes.messages import messages_bp
from routes.feedback import feedback_bp
from routes.verification import verification_bp
from routes.reports import reports_bp
from routes.study_materials import study_materials_bp
from routes.classroom_finder import classroom_finder_bp
from routes.notifications import notifications_bp, mail
import os
from datetime import timedelta, datetime, time, timezone
import json

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '9ae69405bbc6d4d2d93ae932624c4310dfaa3bb8ac100a1427da98ef0ff95c6a')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory SQLite for testing
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
    
    # Email configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Initialize extensions
    db.init_app(app)
    csrf = CSRFProtect(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = 'strong'
    socketio.init_app(app)
    mail.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(classroom_bp, url_prefix='/classroom')
    app.register_blueprint(assignments_bp, url_prefix='/assignments')
    app.register_blueprint(lost_found_bp, url_prefix='/lost-found')
    app.register_blueprint(materials_bp, url_prefix='/materials')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(timetable_bp, url_prefix='/timetable')
    app.register_blueprint(messages_bp, url_prefix='/messages')
    app.register_blueprint(feedback_bp, url_prefix='/feedback')
    app.register_blueprint(verification_bp, url_prefix='/verification')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(study_materials_bp, url_prefix='/study-materials')
    app.register_blueprint(classroom_finder_bp, url_prefix='/classroom-finder')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    
    # Create upload directories
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'assignments'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'submissions'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'materials'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'lost_found'), exist_ok=True)
    
    @app.route('/favicon/<path:filename>')
    def serve_favicon(filename):
        return send_from_directory('favicon', filename)

    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Handle OneSignal service worker requests
    @app.route('/OneSignalSDKWorker.js')
    def onesignal_worker():
        return '', 404
    
    @app.route('/OneSignalSDKUpdaterWorker.js')
    def onesignal_updater_worker():
        return '', 404
    
    @app.route('/clear-onesignal')
    def clear_onesignal():
        return render_template('clear_onesignal.html')
    
    return app

# Create the application instance
app = create_app()

# Initialize database and create admin user
with app.app_context():
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True,
            is_approved=True,
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Created admin user")
    
    # Create default admin role if it doesn't exist
    admin_role = AdminRole.query.filter_by(name='Super Admin').first()
    if not admin_role:
        admin_role = AdminRole(
            name='Super Admin',
            module='all',
            permissions='["all"]',
            description='Super administrator with full access'
        )
        db.session.add(admin_role)
        db.session.commit()
        print("Created default admin role")
    
    # Assign admin role to admin user if not already assigned
    user_role = UserRole.query.filter_by(user_id=admin.id, role_id=admin_role.id).first()
    if not user_role:
        user_role = UserRole(user_id=admin.id, role_id=admin_role.id)
        db.session.add(user_role)
        db.session.commit()
        print("Assigned admin role to admin user")

if __name__ == '__main__':
    socketio.run(app, debug=True)