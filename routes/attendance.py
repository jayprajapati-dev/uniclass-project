from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, AttendanceRecord, AttendanceThreshold, TimetableEntry, User
from datetime import datetime, date
from functools import wraps

attendance_bp = Blueprint('attendance', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_teacher:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@attendance_bp.route('/admin/attendance')
@login_required
@admin_required
def admin_attendance():
    # Get all attendance records
    records = AttendanceRecord.query.order_by(AttendanceRecord.date.desc()).all()
    thresholds = AttendanceThreshold.query.all()
    return render_template('admin/attendance.html', records=records, thresholds=thresholds)

@attendance_bp.route('/admin/attendance/threshold', methods=['POST'])
@login_required
@admin_required
def set_attendance_threshold():
    department = request.form.get('department')
    semester = request.form.get('semester')
    threshold = float(request.form.get('threshold'))
    
    # Update or create threshold
    existing = AttendanceThreshold.query.filter_by(
        department=department,
        semester=semester
    ).first()
    
    if existing:
        existing.threshold_percentage = threshold
    else:
        new_threshold = AttendanceThreshold(
            department=department,
            semester=semester,
            threshold_percentage=threshold
        )
        db.session.add(new_threshold)
    
    db.session.commit()
    flash('Attendance threshold updated successfully.', 'success')
    return redirect(url_for('attendance.admin_attendance'))

@attendance_bp.route('/teacher/attendance')
@login_required
@teacher_required
def teacher_attendance():
    # Get today's classes for the teacher
    today = date.today()
    day_of_week = today.strftime('%A')
    
    classes = TimetableEntry.query.filter_by(
        faculty=current_user.name,
        day_of_week=day_of_week
    ).all()
    
    return render_template('teacher/attendance.html', classes=classes)

@attendance_bp.route('/teacher/attendance/mark/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def mark_attendance(subject_id):
    subject = TimetableEntry.query.get_or_404(subject_id)
    
    if request.method == 'POST':
        # Get student IDs and their attendance status
        student_ids = request.form.getlist('student_id[]')
        statuses = request.form.getlist('status[]')
        
        today = date.today()
        
        # Create attendance records
        for student_id, status in zip(student_ids, statuses):
            record = AttendanceRecord(
                student_id=student_id,
                subject_id=subject_id,
                date=today,
                status=status,
                marked_by=current_user.id
            )
            db.session.add(record)
        
        db.session.commit()
        flash('Attendance marked successfully.', 'success')
        return redirect(url_for('attendance.teacher_attendance'))
    
    # Get all students in the batch
    students = User.query.filter_by(
        role='student',
        department=subject.department,
        year=subject.batch
    ).all()
    
    return render_template('teacher/mark_attendance.html', subject=subject, students=students)

@attendance_bp.route('/student/attendance')
@login_required
def student_attendance():
    # Get student's attendance records
    records = AttendanceRecord.query.filter_by(
        student_id=current_user.id
    ).order_by(AttendanceRecord.date.desc()).all()
    
    # Calculate attendance percentage for each subject
    subject_stats = {}
    for record in records:
        if record.subject_id not in subject_stats:
            subject_stats[record.subject_id] = {
                'total': 0,
                'present': 0,
                'absent': 0,
                'late': 0
            }
        
        stats = subject_stats[record.subject_id]
        stats['total'] += 1
        if record.status == 'present':
            stats['present'] += 1
        elif record.status == 'absent':
            stats['absent'] += 1
        else:
            stats['late'] += 1
    
    # Get attendance threshold
    threshold = AttendanceThreshold.query.filter_by(
        department=current_user.department,
        semester=current_user.semester
    ).first()
    
    return render_template('student/attendance.html',
                         records=records,
                         subject_stats=subject_stats,
                         threshold=threshold)

@attendance_bp.route('/api/attendance/status/<int:subject_id>')
@login_required
def get_attendance_status(subject_id):
    # Get attendance records for the subject
    records = AttendanceRecord.query.filter_by(
        student_id=current_user.id,
        subject_id=subject_id
    ).all()
    
    # Calculate statistics
    total = len(records)
    present = sum(1 for r in records if r.status == 'present')
    absent = sum(1 for r in records if r.status == 'absent')
    late = sum(1 for r in records if r.status == 'late')
    
    # Get threshold
    threshold = AttendanceThreshold.query.filter_by(
        department=current_user.department,
        semester=current_user.semester
    ).first()
    
    return jsonify({
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'percentage': (present / total * 100) if total > 0 else 0,
        'threshold': threshold.threshold_percentage if threshold else 75
    }) 