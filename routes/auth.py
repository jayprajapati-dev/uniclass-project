from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from forms import LoginForm, RegistrationForm
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        print(f"Login attempt for email: {form.email.data}, role: {form.role.data}")  # Debug log
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            print(f"User found: {user.email}, role: {user.role}")  # Debug log
            if check_password_hash(user.password_hash, form.password.data):
                print("Password check passed")  # Debug log
                # Check if the selected role matches the user's role
                if user.role != form.role.data:
                    print(f"Role mismatch: user role={user.role}, selected role={form.role.data}")  # Debug log
                    flash('Invalid role selected for this account', 'danger')
                    return render_template('auth/login.html', form=form)
                    
                if not user.is_active:
                    flash('Your account has been deactivated. Please contact support.', 'danger')
                    return render_template('auth/login.html', form=form)
                
                # Check if teacher is approved
                if user.role == 'teacher' and not user.is_approved:
                    flash('Your account is pending admin approval. Please wait for approval.', 'warning')
                    return render_template('auth/login.html', form=form)
                
                login_user(user, remember=form.remember.data, duration=timedelta(days=7))
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                if user.role == 'admin':
                    return redirect(url_for('admin.index'))
                elif user.role == 'teacher':
                    return redirect(url_for('teacher.index'))
                else:
                    return redirect(url_for('main.index'))
            else:
                print("Password check failed")  # Debug log
        else:
            print(f"No user found with email: {form.email.data}")  # Debug log
        flash('Invalid email or password', 'danger')
    elif form.errors:
        print(f"Form validation errors: {form.errors}")  # Debug log
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.title()}: {error}', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if email already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Check if mobile number already exists
        if User.query.filter_by(mobile=form.mobile.data).first():
            flash('Mobile number already registered', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.name.data.lower().replace(' ', '_'),  # Create username from name
            name=form.name.data,  # Set the name field
            email=form.email.data,
            mobile=form.mobile.data,
            password_hash=generate_password_hash(form.password.data),
            role=form.role.data,
            department=form.department.data if form.role.data == 'student' else None,
            year=form.year.data if form.role.data == 'student' else None,
            is_approved=form.role.data == 'student'  # Auto-approve students, teachers need admin approval
        )
        
        db.session.add(user)
        db.session.commit()
        
        if user.role == 'teacher':
            flash('Registration successful! Please wait for admin approval.', 'info')
            return redirect(url_for('auth.login'))
        else:
            # Auto-login students after registration
            login_user(user)
            flash('Registration successful! Welcome to UniClass.', 'success')
            return redirect(url_for('main.index'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = RegistrationForm(obj=current_user)
    if request.method == 'POST':
        if 'update_profile' in request.form:
            current_user.name = request.form.get('name')
            if current_user.is_student:
                current_user.department = request.form.get('department')
                current_user.year = request.form.get('year')
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        elif 'change_password' in request.form:
            if current_user.check_password(request.form.get('current_password')):
                current_user.set_password(request.form.get('new_password'))
                db.session.commit()
                flash('Password changed successfully!', 'success')
            else:
                flash('Current password is incorrect.', 'danger')
    return render_template('auth/profile.html', form=form)

@auth_bp.route('/users')
@login_required
def view_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    return render_template('auth/users.html', users=users) 