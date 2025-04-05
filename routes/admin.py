from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps
from models import db, User, Classroom, TimetableEntry, Assignment, AssignmentSubmission, AdminRole, UserRole
from forms import AddTeacherForm
import json
import os
import shutil

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def index():
    users = User.query.all()
    classrooms = Classroom.query.all()
    assignments = Assignment.query.all()
    pending_teachers = User.query.filter_by(role='teacher', is_approved=False).all()
    return render_template('admin/index.html', 
                         users=users, 
                         classrooms=classrooms, 
                         assignments=assignments,
                         pending_teachers=pending_teachers,
                         now=datetime.now())

@admin_bp.route('/users')
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/add', methods=['POST'])
@admin_required
def add_user():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'danger')
        return redirect(url_for('admin.users'))

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash('User added successfully.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    user.name = request.form.get('name')
    user.email = request.form.get('email')
    user.role = request.form.get('role')
    user.is_active = 'is_active' in request.form
    
    db.session.commit()
    flash('User updated successfully.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/classrooms')
@admin_required
def classrooms():
    classrooms = Classroom.query.all()
    return render_template('admin/classrooms.html', classrooms=classrooms)

@admin_bp.route('/classrooms/add', methods=['POST'])
@admin_required
def add_classroom():
    name = request.form.get('name')
    location = request.form.get('location')
    room_type = request.form.get('room_type')
    department = request.form.get('department')
    capacity = request.form.get('capacity')
    is_active = 'is_active' in request.form

    classroom = Classroom(
        name=name,
        location=location,
        room_type=room_type,
        department=department,
        capacity=capacity,
        is_active=is_active
    )
    
    db.session.add(classroom)
    db.session.commit()
    
    flash('Classroom added successfully.', 'success')
    return redirect(url_for('admin.classrooms'))

@admin_bp.route('/classrooms/<int:classroom_id>/edit', methods=['POST'])
@admin_required
def edit_classroom(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    
    classroom.name = request.form.get('name')
    classroom.location = request.form.get('location')
    classroom.room_type = request.form.get('room_type')
    classroom.department = request.form.get('department')
    classroom.capacity = request.form.get('capacity')
    classroom.is_active = 'is_active' in request.form
    
    db.session.commit()
    flash('Classroom updated successfully.', 'success')
    return redirect(url_for('admin.classrooms'))

@admin_bp.route('/classrooms/<int:classroom_id>/delete', methods=['POST'])
@admin_required
def delete_classroom(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    
    db.session.delete(classroom)
    db.session.commit()
    flash('Classroom deleted successfully.', 'success')
    return redirect(url_for('admin.classrooms'))

@admin_bp.route('/timetable')
@admin_required
def timetable():
    entries = TimetableEntry.query.all()
    classrooms = Classroom.query.all()
    teachers = User.query.filter_by(role='teacher').all()
    
    classroom_id = request.args.get('classroom', type=int)
    teacher_id = request.args.get('teacher', type=int)
    day = request.args.get('day')
    
    if classroom_id:
        entries = [e for e in entries if e.classroom_id == classroom_id]
    if teacher_id:
        entries = [e for e in entries if e.teacher_id == teacher_id]
    if day:
        entries = [e for e in entries if e.day == day]
    
    return render_template('admin/timetable.html', entries=entries, classrooms=classrooms, teachers=teachers)

@admin_bp.route('/timetable/add', methods=['POST'])
@admin_required
def add_timetable_entry():
    day = request.form.get('day')
    start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
    end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
    classroom_id = request.form.get('classroom_id')
    teacher_id = request.form.get('teacher_id')
    subject = request.form.get('subject')

    entry = TimetableEntry(
        day=day,
        start_time=start_time,
        end_time=end_time,
        classroom_id=classroom_id,
        teacher_id=teacher_id,
        subject=subject
    )
    
    db.session.add(entry)
    db.session.commit()
    
    flash('Timetable entry added successfully.', 'success')
    return redirect(url_for('admin.timetable'))

@admin_bp.route('/timetable/<int:entry_id>/edit', methods=['POST'])
@admin_required
def edit_timetable_entry(entry_id):
    entry = TimetableEntry.query.get_or_404(entry_id)
    
    entry.day = request.form.get('day')
    entry.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
    entry.end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
    entry.classroom_id = request.form.get('classroom_id')
    entry.teacher_id = request.form.get('teacher_id')
    entry.subject = request.form.get('subject')
    
    db.session.commit()
    flash('Timetable entry updated successfully.', 'success')
    return redirect(url_for('admin.timetable'))

@admin_bp.route('/timetable/<int:entry_id>/delete', methods=['POST'])
@admin_required
def delete_timetable_entry(entry_id):
    entry = TimetableEntry.query.get_or_404(entry_id)
    
    db.session.delete(entry)
    db.session.commit()
    flash('Timetable entry deleted successfully.', 'success')
    return redirect(url_for('admin.timetable'))

@admin_bp.route('/assignments')
@admin_required
def assignments():
    assignments = Assignment.query.all()
    teachers = User.query.filter_by(role='teacher').all()
    
    teacher_id = request.args.get('teacher', type=int)
    status = request.args.get('status')
    
    if teacher_id:
        assignments = [a for a in assignments if a.teacher_id == teacher_id]
    if status:
        now = datetime.now()
        if status == 'active':
            assignments = [a for a in assignments if a.due_date > now]
        elif status == 'expired':
            assignments = [a for a in assignments if a.due_date <= now]
    
    return render_template('admin/assignments.html', assignments=assignments, teachers=teachers, now=datetime.now())

@admin_bp.route('/assignments/add', methods=['POST'])
@admin_required
def add_assignment():
    title = request.form.get('title')
    description = request.form.get('description')
    teacher_id = request.form.get('teacher_id')
    due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%dT%H:%M')

    assignment = Assignment(
        title=title,
        description=description,
        teacher_id=teacher_id,
        due_date=due_date
    )
    
    db.session.add(assignment)
    db.session.commit()
    
    flash('Assignment added successfully.', 'success')
    return redirect(url_for('admin.assignments'))

@admin_bp.route('/assignments/<int:assignment_id>/edit', methods=['POST'])
@admin_required
def edit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    assignment.title = request.form.get('title')
    assignment.description = request.form.get('description')
    assignment.teacher_id = request.form.get('teacher_id')
    assignment.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%dT%H:%M')
    
    db.session.commit()
    flash('Assignment updated successfully.', 'success')
    return redirect(url_for('admin.assignments'))

@admin_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@admin_required
def delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    db.session.delete(assignment)
    db.session.commit()
    flash('Assignment deleted successfully.', 'success')
    return redirect(url_for('admin.assignments'))

@admin_bp.route('/teachers/add', methods=['GET', 'POST'])
@admin_required
def add_teacher():
    form = AddTeacherForm()
    if form.validate_on_submit():
        teacher = User(
            username=form.username.data,
            email=form.email.data,
            name=form.name.data,
            role='teacher',
            is_approved=True
        )
        teacher.set_password(form.password.data)
        db.session.add(teacher)
        db.session.commit()
        flash('Teacher account created successfully!', 'success')
        return redirect(url_for('admin.index'))
    return render_template('admin/add_teacher.html', form=form)

@admin_bp.route('/teachers')
@admin_required
def manage_teachers():
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('admin/teachers.html', teachers=teachers)

@admin_bp.route('/pending-teachers')
@admin_required
def pending_teachers():
    pending_teachers = User.query.filter_by(role='teacher', is_approved=False).all()
    return render_template('admin/pending_teachers.html', teachers=pending_teachers)

@admin_bp.route('/approve-teacher/<int:user_id>', methods=['POST'])
@admin_required
def approve_teacher(user_id):
    teacher = User.query.get_or_404(user_id)
    if teacher.role != 'teacher':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('admin.pending_teachers'))
    
    teacher.is_approved = True
    db.session.commit()
    flash(f'Teacher {teacher.username} has been approved.', 'success')
    return redirect(url_for('admin.pending_teachers'))

@admin_bp.route('/reject-teacher/<int:user_id>', methods=['POST'])
@admin_required
def reject_teacher(user_id):
    teacher = User.query.get_or_404(user_id)
    if teacher.role != 'teacher':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('admin.pending_teachers'))
    
    reason = request.form.get('reason', '')
    
    # Mark the teacher as rejected instead of deleting
    teacher.is_approved = False
    teacher.is_active = False  # Optionally deactivate the account
    db.session.commit()
    
    flash(f'Teacher {teacher.username} has been rejected.', 'success')
    return redirect(url_for('admin.pending_teachers'))

@admin_bp.route('/delete-teacher/<int:user_id>', methods=['POST'])
@admin_required
def delete_pending_teacher(user_id):
    teacher = User.query.get_or_404(user_id)
    if teacher.role != 'teacher':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('admin.pending_teachers'))
    
    # Delete the teacher account
    db.session.delete(teacher)
    db.session.commit()
    
    flash(f'Teacher {teacher.username} has been deleted.', 'success')
    return redirect(url_for('admin.pending_teachers'))

@admin_bp.route('/teachers/<int:teacher_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_teacher(teacher_id):
    teacher = User.query.get_or_404(teacher_id)
    if teacher.role != 'teacher':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('admin.manage_teachers'))
    
    if request.method == 'POST':
        teacher.name = request.form.get('name')
        teacher.username = request.form.get('username')
        teacher.email = request.form.get('email')
        teacher.department = request.form.get('department')
        
        if request.form.get('password'):
            teacher.set_password(request.form.get('password'))
        
        db.session.commit()
        flash('Teacher updated successfully.', 'success')
        return redirect(url_for('admin.manage_teachers'))
    
    return render_template('admin/edit_teacher.html', teacher=teacher)

@admin_bp.route('/teachers/<int:teacher_id>/delete', methods=['POST'])
@admin_required
def delete_teacher(teacher_id):
    teacher = User.query.get_or_404(teacher_id)
    if teacher.role != 'teacher':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('admin.manage_teachers'))
    
    # Delete associated assignments
    Assignment.query.filter_by(created_by=teacher_id).delete()
    
    # Delete the teacher
    db.session.delete(teacher)
    db.session.commit()
    
    flash('Teacher deleted successfully.', 'success')
    return redirect(url_for('admin.manage_teachers'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        # Update system settings
        settings = {
            'site_name': request.form.get('site_name'),
            'site_description': request.form.get('site_description'),
            'contact_email': request.form.get('contact_email'),
            'maintenance_mode': 'maintenance_mode' in request.form,
            'allow_registration': 'allow_registration' in request.form,
            'require_approval': 'require_approval' in request.form,
            'max_upload_size': request.form.get('max_upload_size'),
            'session_timeout': request.form.get('session_timeout')
        }
        
        # Save settings to file
        with open('config/settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))
    
    # Load current settings
    try:
        with open('config/settings.json', 'r') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {
            'site_name': 'UniClass',
            'site_description': 'Student Information Portal',
            'contact_email': 'admin@example.com',
            'maintenance_mode': False,
            'allow_registration': True,
            'require_approval': True,
            'max_upload_size': 10,
            'session_timeout': 30
        }
    
    return render_template('admin/settings.html', settings=settings)

@admin_bp.route('/backup', methods=['GET', 'POST'])
@admin_required
def backup():
    if request.method == 'POST':
        try:
            # Create backup directory
            backup_dir = 'backups'
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f'backup_{timestamp}.db'
            backup_path = os.path.join(backup_dir, backup_file)
            
            # Copy database file
            shutil.copy2('instance/app.db', backup_path)
            
            flash(f'Backup created successfully: {backup_file}', 'success')
        except Exception as e:
            flash(f'Error creating backup: {str(e)}', 'danger')
        
        return redirect(url_for('admin.backup'))
    
    # List existing backups
    backup_dir = 'backups'
    backups = []
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.startswith('backup_') and file.endswith('.db'):
                path = os.path.join(backup_dir, file)
                backups.append({
                    'filename': file,
                    'size': os.path.getsize(path),
                    'created': datetime.fromtimestamp(os.path.getctime(path))
                })
    
    return render_template('admin/backup.html', backups=backups)

@admin_bp.route('/restore/<filename>', methods=['POST'])
@admin_required
def restore(filename):
    try:
        backup_path = os.path.join('backups', filename)
        if not os.path.exists(backup_path):
            flash('Backup file not found.', 'danger')
            return redirect(url_for('admin.backup'))
        
        # Create a temporary backup of current database
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_backup = f'temp_backup_{timestamp}.db'
        shutil.copy2('instance/app.db', os.path.join('backups', temp_backup))
        
        # Restore from backup
        shutil.copy2(backup_path, 'instance/app.db')
        
        flash('Database restored successfully.', 'success')
    except Exception as e:
        flash(f'Error restoring backup: {str(e)}', 'danger')
    
    return redirect(url_for('admin.backup'))

@admin_bp.route('/delete-backup/<filename>', methods=['POST'])
@admin_required
def delete_backup(filename):
    try:
        backup_path = os.path.join('backups', filename)
        if os.path.exists(backup_path):
            os.remove(backup_path)
            flash('Backup deleted successfully.', 'success')
        else:
            flash('Backup file not found.', 'danger')
    except Exception as e:
        flash(f'Error deleting backup: {str(e)}', 'danger')
    
    return redirect(url_for('admin.backup')) 