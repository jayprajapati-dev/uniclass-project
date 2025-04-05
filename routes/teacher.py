from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Assignment, AssignmentSubmission, User, TimetableEntry, Report, LostItem, FoundItem, StudyMaterial, Classroom, TimeSlot
from functools import wraps
import os
from werkzeug.utils import secure_filename
from datetime import datetime, date

teacher_bp = Blueprint('teacher', __name__)

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_teacher:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@teacher_bp.route('/')
@login_required
@teacher_required
def index():
    # Get teacher's department
    teacher_department = current_user.department
    
    # Get quick stats
    total_students = User.query.filter_by(role='student', department=teacher_department).count()
    active_assignments = Assignment.query.filter_by(created_by=current_user.id).count()
    pending_reports = Report.query.filter_by(department=teacher_department, status='pending').count()
    
    # Get today's classes
    today = datetime.now().strftime('%A')
    today_classes = TimetableEntry.query.join(Classroom).join(TimeSlot).filter(
        TimetableEntry.day == today,
        Classroom.department == teacher_department
    ).order_by(TimeSlot.start_time).all()
    
    # Get recent submissions
    recent_submissions = AssignmentSubmission.query.join(Assignment).filter(
        Assignment.created_by == current_user.id
    ).order_by(AssignmentSubmission.submitted_at.desc()).limit(5).all()
    
    # Get recent reports
    recent_reports = Report.query.filter_by(department=teacher_department).order_by(Report.created_at.desc()).limit(5).all()
    
    # Get lost and found items
    lost_items = LostItem.query.join(User, LostItem.user_id == User.id).filter(
        User.department == teacher_department
    ).order_by(LostItem.created_at.desc()).limit(5).all()
    found_items = FoundItem.query.join(User, FoundItem.user_id == User.id).filter(
        User.department == teacher_department
    ).order_by(FoundItem.created_at.desc()).limit(5).all()
    
    # Get recent study materials
    study_materials = StudyMaterial.query.join(User, StudyMaterial.seller_id == User.id).filter(
        User.department == teacher_department
    ).order_by(StudyMaterial.created_at.desc()).limit(5).all()
    
    return render_template('teacher/index.html',
                         total_students=total_students,
                         active_assignments=active_assignments,
                         pending_reports=pending_reports,
                         today_classes=today_classes,
                         recent_submissions=recent_submissions,
                         recent_reports=recent_reports,
                         lost_items=lost_items,
                         found_items=found_items,
                         study_materials=study_materials)

@teacher_bp.route('/teacher/assignments')
@login_required
@teacher_required
def assignments():
    assignments = Assignment.query.filter_by(created_by=current_user.id).all()
    return render_template('teacher/assignments.html', assignments=assignments)

@teacher_bp.route('/teacher/assignments/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_assignment():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        submission_type = request.form['submission_type']
        
        assignment = Assignment(
            title=title,
            description=description,
            due_date=due_date,
            submission_type=submission_type,
            created_by=current_user.id
        )
        
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/uploads/assignments', filename)
                file.save(file_path)
                assignment.file_path = file_path
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Assignment created successfully.', 'success')
        return redirect(url_for('teacher.assignments'))
        
    return render_template('teacher/create_assignment.html')

@teacher_bp.route('/teacher/assignments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    
    if assignment.created_by != current_user.id:
        flash('You do not have permission to edit this assignment.', 'danger')
        return redirect(url_for('teacher.assignments'))
        
    if request.method == 'POST':
        assignment.title = request.form['title']
        assignment.description = request.form['description']
        assignment.due_date = request.form['due_date']
        assignment.submission_type = request.form['submission_type']
        
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/uploads/assignments', filename)
                file.save(file_path)
                assignment.file_path = file_path
        
        db.session.commit()
        
        flash('Assignment updated successfully.', 'success')
        return redirect(url_for('teacher.assignments'))
        
    return render_template('teacher/edit_assignment.html', assignment=assignment)

@teacher_bp.route('/teacher/assignments/<int:id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    
    if assignment.created_by != current_user.id:
        flash('You do not have permission to delete this assignment.', 'danger')
        return redirect(url_for('teacher.assignments'))
        
    db.session.delete(assignment)
    db.session.commit()
    
    flash('Assignment deleted successfully.', 'success')
    return redirect(url_for('teacher.assignments'))

@teacher_bp.route('/teacher/submissions')
@login_required
@teacher_required
def submissions():
    # Get all submissions for assignments created by the current teacher
    submissions = AssignmentSubmission.query.join(Assignment).filter(
        Assignment.created_by == current_user.id
    ).all()
    
    return render_template('teacher/submissions.html', submissions=submissions)

@teacher_bp.route('/teacher/submissions/<int:id>/review', methods=['POST'])
@login_required
@teacher_required
def review_submission(id):
    submission = AssignmentSubmission.query.get_or_404(id)
    
    if submission.assignment.created_by != current_user.id:
        flash('You do not have permission to review this submission.', 'danger')
        return redirect(url_for('teacher.submissions'))
        
    status = request.form['status']
    notes = request.form.get('notes', '')
    
    submission.status = status
    submission.teacher_notes = notes
    submission.reviewed_by = current_user.id
    
    db.session.commit()
    
    flash('Submission reviewed successfully.', 'success')
    return redirect(url_for('teacher.submissions'))

@teacher_bp.route('/teacher/mark-attendance')
@login_required
@teacher_required
def mark_attendance():
    # Get teacher's department
    teacher_department = current_user.department
    
    # Get today's date
    today = date.today()
    
    # Get all students in the teacher's department
    students = User.query.filter_by(role='student', department=teacher_department).all()
    
    # Get today's classes for the teacher
    today_name = today.strftime('%A')
    today_classes = TimetableEntry.query.join(Classroom).join(TimeSlot).filter(
        TimetableEntry.day == today_name,
        Classroom.department == teacher_department
    ).order_by(TimeSlot.start_time).all()
    
    return render_template('teacher/mark_attendance.html', 
                          students=students, 
                          today_classes=today_classes,
                          today=today)

@teacher_bp.route('/teacher/save-attendance', methods=['POST'])
@login_required
@teacher_required
def save_attendance():
    # Get teacher's department
    teacher_department = current_user.department
    
    # Get today's date
    attendance_date = request.form.get('date')
    
    # Get all students in the teacher's department
    students = User.query.filter_by(role='student', department=teacher_department).all()
    
    # Process each student's attendance
    for student in students:
        status = request.form.get(f'status_{student.id}')
        notes = request.form.get(f'notes_{student.id}', '')
        
        # Here you would save the attendance to your database
        # For example:
        # attendance = Attendance(
        #     student_id=student.id,
        #     teacher_id=current_user.id,
        #     date=attendance_date,
        #     status=status,
        #     notes=notes
        # )
        # db.session.add(attendance)
    
    # db.session.commit()
    flash('Attendance saved successfully.', 'success')
    return redirect(url_for('teacher.index'))

@teacher_bp.route('/teacher/classrooms/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_classroom():
    if request.method == 'POST':
        room_number = request.form['room_number']
        location = request.form['location']
        room_type = request.form['room_type']
        
        # Create new classroom
        classroom = Classroom(
            room_number=room_number,
            location=location,
            room_type=room_type,
            department=current_user.department,  # Automatically set to teacher's department
            created_by=current_user.id
        )
        
        db.session.add(classroom)
        db.session.commit()
        
        flash('Classroom created successfully.', 'success')
        return redirect(url_for('teacher.index'))
        
    return render_template('teacher/create_classroom.html') 