from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Classroom, TimetableEntry, RoomReport, TimeSlot
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from forms import ClassroomSearchForm

classroom_finder_bp = Blueprint('classroom_finder', __name__)

@classroom_finder_bp.route('/classroom-finder')
def index():
    form = ClassroomSearchForm()
    
    # Standard departments
    departments = [
        ('CE', 'Civil Engineering (CE)'),
        ('ME', 'Mechanical Engineering (ME)'),
        ('EE', 'Electrical Engineering (EE)'),
        ('EC', 'Electronics & Communication Engineering (EC)'),
        ('IT', 'Information Technology (IT)'),
        ('ICT', 'Information and Communication Technology (ICT)')
    ]
    
    # Standard room types
    room_types = ['lecture_room', 'lab_room', 'computer_room', 'working_room']
    
    # Get current time and day of week
    now = datetime.now()
    current_time = now.time()
    current_day = now.strftime('%A')
    
    # Get filter parameters
    department = request.args.get('department', '')
    room_type = request.args.get('room_type', '')
    search = request.args.get('search', '')
    
    # Start with base query for active classrooms
    query = Classroom.query.filter_by(is_active=True)
    
    # Apply filters
    if department:
        query = query.filter_by(department=department)
    if room_type:
        query = query.filter_by(room_type=room_type)
    if search:
        query = query.filter(
            or_(
                Classroom.name.ilike(f'%{search}%'),
                Classroom.location.ilike(f'%{search}%')
            )
        )
    
    # Get filtered classrooms
    classrooms = query.all()
    
    # Get current timetable entries
    current_entries = TimetableEntry.query.join(TimeSlot).filter(
        and_(
            TimetableEntry.day == current_day,
            TimeSlot.start_time <= current_time,
            TimeSlot.end_time >= current_time
        )
    ).all()
    
    # Create a set of occupied classroom IDs
    occupied_classrooms = {entry.classroom_id for entry in current_entries}
    
    # Get pending reports
    pending_reports = RoomReport.query.filter_by(status='pending').all()
    reported_classrooms = {report.classroom_id for report in pending_reports}
    
    # Combine occupied and reported classrooms
    unavailable_classrooms = occupied_classrooms | reported_classrooms
    
    return render_template('classrooms/index.html',
                         form=form,
                         classrooms=classrooms,
                         unavailable_classrooms=unavailable_classrooms,
                         departments=departments,
                         room_types=room_types,
                         current_time=current_time,
                         selected_department=department,
                         selected_room_type=room_type,
                         search_term=search)

@classroom_finder_bp.route('/api/classroom-status/<int:classroom_id>')
def get_classroom_status(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    
    # Get current time and day of week
    now = datetime.now()
    current_time = now.time()
    current_day = now.strftime('%A')
    
    # Check if classroom is occupied by timetable
    current_entry = TimetableEntry.query.join(TimeSlot).filter(
        and_(
            TimetableEntry.classroom_id == classroom_id,
            TimetableEntry.day == current_day,
            TimeSlot.start_time <= current_time,
            TimeSlot.end_time >= current_time
        )
    ).first()
    
    # Check if classroom has pending reports
    pending_report = RoomReport.query.filter(
        and_(
            RoomReport.classroom_id == classroom_id,
            RoomReport.status == 'pending'
        )
    ).first()
    
    if current_entry:
        time_remaining = (current_entry.time_slot.end_time - current_time).total_seconds() / 60
        return jsonify({
            'status': 'occupied',
            'subject': current_entry.subject.name if current_entry.subject else 'Unknown',
            'professor': current_entry.subject.teacher.name if current_entry.subject and current_entry.subject.teacher else 'Unknown',
            'end_time': current_entry.time_slot.end_time.strftime('%H:%M'),
            'time_remaining': f"{int(time_remaining)} minutes"
        })
    elif pending_report:
        return jsonify({
            'status': 'reported',
            'report_type': pending_report.report_type,
            'description': pending_report.description
        })
    else:
        # Get next class if any
        next_entry = TimetableEntry.query.join(TimeSlot).filter(
            and_(
                TimetableEntry.classroom_id == classroom_id,
                TimetableEntry.day == current_day,
                TimeSlot.start_time > current_time
            )
        ).order_by(TimeSlot.start_time).first()
        
        return jsonify({
            'status': 'available',
            'next_class': {
                'subject': next_entry.subject.name if next_entry and next_entry.subject else None,
                'professor': next_entry.subject.teacher.name if next_entry and next_entry.subject and next_entry.subject.teacher else None,
                'start_time': next_entry.time_slot.start_time.strftime('%H:%M') if next_entry else None
            } if next_entry else None
        })

@classroom_finder_bp.route('/api/report-classroom', methods=['POST'])
@login_required
def report_classroom():
    data = request.get_json()
    classroom_id = data.get('classroom_id')
    report_type = data.get('report_type')
    description = data.get('description')
    
    if not all([classroom_id, report_type]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    report = RoomReport(
        classroom_id=classroom_id,
        user_id=current_user.id,
        report_type=report_type,
        description=description
    )
    
    db.session.add(report)
    db.session.commit()
    
    return jsonify({'message': 'Report submitted successfully'})

@classroom_finder_bp.route('/api/filter-classrooms')
def filter_classrooms():
    department = request.args.get('department')
    room_type = request.args.get('room_type')
    
    query = Classroom.query.filter_by(is_active=True)
    
    if department:
        query = query.filter_by(department=department)
    if room_type:
        query = query.filter_by(room_type=room_type)
    
    classrooms = query.all()
    
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'location': c.location,
        'room_type': c.room_type,
        'department': c.department,
        'capacity': c.capacity
    } for c in classrooms]) 