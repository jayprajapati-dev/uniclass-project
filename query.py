from models import db, User, Classroom, Assignment, AssignmentSubmission, TimetableEntry
from datetime import datetime, timedelta

def get_active_classrooms():
    """Get all active classrooms."""
    return Classroom.query.filter_by(is_active=True).all()

def get_classroom_by_id(classroom_id):
    """Get a classroom by its ID."""
    return Classroom.query.get_or_404(classroom_id)

def get_classrooms_by_department(department):
    """Get all classrooms for a specific department."""
    return Classroom.query.filter_by(department=department).all()

def get_classrooms_by_type(room_type):
    """Get all classrooms of a specific type."""
    return Classroom.query.filter_by(room_type=room_type).all()

def get_classrooms_by_capacity(min_capacity):
    """Get all classrooms with capacity greater than or equal to min_capacity."""
    return Classroom.query.filter(Classroom.capacity >= min_capacity).all()

def get_timetable_entries(classroom_id, day=None):
    """Get timetable entries for a classroom, optionally filtered by day."""
    query = TimetableEntry.query.filter_by(classroom_id=classroom_id)
    if day:
        query = query.filter_by(day_of_week=day)
    return query.order_by(TimetableEntry.start_time).all()

def get_current_classroom_status(classroom_id):
    """Get the current status of a classroom (occupied or available)."""
    now = datetime.now()
    current_time = now.time()
    current_day = now.strftime('%A')  # Get current day name
    
    # Get today's entries for the classroom
    entries = TimetableEntry.query.filter_by(
        classroom_id=classroom_id,
        day_of_week=current_day
    ).order_by(TimetableEntry.start_time).all()
    
    # Check if any entry is currently active
    for entry in entries:
        if entry.start_time <= current_time <= entry.end_time:
            return {
                'status': 'occupied',
                'subject': entry.subject,
                'faculty': entry.faculty,
                'batch': entry.batch,
                'end_time': entry.end_time
            }
    
    # If no current entry, find the next entry
    next_entry = TimetableEntry.query.filter(
        TimetableEntry.classroom_id == classroom_id,
        TimetableEntry.day_of_week == current_day,
        TimetableEntry.start_time > current_time
    ).order_by(TimetableEntry.start_time).first()
    
    if next_entry:
        return {
            'status': 'available',
            'next_class': {
                'subject': next_entry.subject,
                'start_time': next_entry.start_time
            }
        }
    
    return {'status': 'available', 'next_class': None}

def get_assignments_by_teacher(teacher_id):
    """Get all assignments created by a specific teacher."""
    return Assignment.query.filter_by(created_by=teacher_id).all()

def get_assignments_by_student(student_id):
    """Get all assignments for a specific student."""
    submissions = AssignmentSubmission.query.filter_by(student_id=student_id).all()
    return [submission.assignment for submission in submissions]

def get_pending_submissions(teacher_id):
    """Get all pending submissions for assignments created by a teacher."""
    return AssignmentSubmission.query.join(Assignment).filter(
        Assignment.created_by == teacher_id,
        AssignmentSubmission.status == 'pending'
    ).all()

def get_submission_status(assignment_id, student_id):
    """Get the submission status for a specific assignment and student."""
    submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id,
        student_id=student_id
    ).first()
    return submission.status if submission else None

def get_upcoming_assignments(student_id, days=7):
    """Get upcoming assignments for a student within the specified number of days."""
    now = datetime.now()
    future_date = now + timedelta(days=days)
    
    return Assignment.query.filter(
        Assignment.due_date > now,
        Assignment.due_date <= future_date
    ).all()

def get_student_submissions(student_id):
    """Get all submissions by a student."""
    return AssignmentSubmission.query.filter_by(student_id=student_id).all()

def get_teacher_submissions(teacher_id):
    """Get all submissions for assignments created by a teacher."""
    return AssignmentSubmission.query.join(Assignment).filter(
        Assignment.created_by == teacher_id
    ).all() 