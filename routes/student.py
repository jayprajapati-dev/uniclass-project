from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Assignment, AssignmentSubmission, TimetableEntry, Classroom, StudyMaterial
from functools import wraps
from datetime import datetime
import os
from werkzeug.utils import secure_filename

student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/student')
@login_required
@student_required
def index():
    # Get assignments
    assignments = Assignment.query.all()
    submissions = AssignmentSubmission.query.filter_by(student_id=current_user.id).all()
    
    # Get today's timetable entries
    today = datetime.now().strftime('%A').lower()
    timetable_entries = TimetableEntry.query\
        .join(Classroom)\
        .filter(
            Classroom.department == current_user.department,
            TimetableEntry.day == today
        ).all()
    
    # Get available study materials
    materials = StudyMaterial.query.filter_by(status='available').all()
    
    return render_template('student/index.html', 
                         assignments=assignments,
                         submissions=submissions,
                         timetable_entries=timetable_entries,
                         materials=materials,
                         now=datetime.now)

@student_bp.route('/student/assignments')
@login_required
@student_required
def assignments():
    assignments = Assignment.query.all()
    submissions = {s.assignment_id: s for s in AssignmentSubmission.query.filter_by(student_id=current_user.id).all()}
    return render_template('student/assignments.html', 
                         assignments=assignments,
                         submissions=submissions)

@student_bp.route('/student/assignments/<int:id>/submit', methods=['GET', 'POST'])
@login_required
@student_required
def submit_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    
    # Check if already submitted
    existing_submission = AssignmentSubmission.query.filter_by(
        assignment_id=id,
        student_id=current_user.id
    ).first()
    
    if existing_submission and existing_submission.status != 'rejected':
        flash('You have already submitted this assignment.', 'warning')
        return redirect(url_for('student.assignments'))
    
    if request.method == 'POST':
        file = request.files.get('file')
        notes = request.form.get('notes', '')
        
        if assignment.submission_type == 'digital' and not file:
            flash('Please upload a file.', 'danger')
            return redirect(url_for('student.submit_assignment', id=id))
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('static/uploads/assignments', filename)
            file.save(file_path)
        else:
            file_path = None
            
        if existing_submission:
            # Update existing submission if it was rejected
            existing_submission.file_path = file_path
            existing_submission.notes = notes
            existing_submission.status = 'pending'
            existing_submission.teacher_notes = None
            existing_submission.reviewed_at = None
            existing_submission.reviewed_by = None
        else:
            # Create new submission
            submission = AssignmentSubmission(
                assignment_id=id,
                student_id=current_user.id,
                file_path=file_path,
                notes=notes
            )
            db.session.add(submission)
            
        db.session.commit()
        flash('Assignment submitted successfully.', 'success')
        return redirect(url_for('student.assignments'))
        
    return render_template('student/submit_assignment.html', assignment=assignment)

@student_bp.route('/student/submissions')
@login_required
@student_required
def submissions():
    submissions = AssignmentSubmission.query.filter_by(student_id=current_user.id).all()
    return render_template('student/submissions.html', submissions=submissions) 