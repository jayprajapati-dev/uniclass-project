from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Classroom, TimetableEntry
from datetime import datetime, timedelta
from sqlalchemy import distinct

classroom_bp = Blueprint('classroom', __name__)

def create_demo_data():
    """Create demo data if no data exists"""
    try:
        # Check if any data exists
        if Classroom.query.first() is not None:
            print("Demo data already exists, skipping...")
            return

        # Create demo classroom
        lab_201 = Classroom(
            name='Lab 201',
            location='Building A, 2nd Floor',
            type='Laboratory',
            department='Computer Science',
            is_active=True
        )
        db.session.add(lab_201)
        db.session.commit()

        # Create demo time slots
        time_slots = [
            ('09:00', '10:00'),
            ('10:00', '11:00'),
            ('11:00', '12:00'),
            ('12:00', '13:00'),
            ('13:00', '14:00'),
            ('14:00', '15:00'),
            ('15:00', '16:00')
        ]

        # Create demo subjects with faculty and batch
        subjects = [
            ('Programming Lab', 'Dr. Smith', 'CS Semester 1'),
            ('Database Lab', 'Dr. Johnson', 'CS Semester 2'),
            ('Network Lab', 'Dr. Williams', 'CS Semester 3'),
            ('AI Lab', 'Dr. Brown', 'CS Semester 4'),
            ('Web Development Lab', 'Dr. Davis', 'CS Semester 1'),
            ('Machine Learning Lab', 'Dr. Wilson', 'CS Semester 3'),
            ('Cloud Computing Lab', 'Dr. Anderson', 'CS Semester 4')
        ]

        # Create timetable entries for each day
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        for day in days:
            for i, (start_time, end_time) in enumerate(time_slots):
                subject, faculty, batch = subjects[i % len(subjects)]
                entry = TimetableEntry(
                    classroom_id=lab_201.id,
                    day_of_week=day,
                    start_time=datetime.strptime(start_time, '%H:%M').time(),
                    end_time=datetime.strptime(end_time, '%H:%M').time(),
                    subject=subject,
                    faculty=faculty,
                    batch=batch
                )
                db.session.add(entry)

        db.session.commit()
        print("Demo data created successfully!")
    except Exception as e:
        print(f"Error creating demo data: {str(e)}")
        db.session.rollback()

@classroom_bp.route('/')
def index():
    # Only create demo data if explicitly requested
    if request.args.get('create_demo') == 'true':
        create_demo_data()
    
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('classroom.admin_dashboard'))
    
    department = request.args.get('department', '')
    room_type = request.args.get('room_type', '')
    
    query = Classroom.query.filter_by(is_active=True)
    
    if department:
        query = query.filter(Classroom.department.ilike(f'%{department}%'))
    if room_type:
        query = query.filter_by(room_type=room_type)
        
    # Get all departments for the filter dropdown
    departments = db.session.query(distinct(Classroom.department)).all()
    departments = [dept[0] for dept in departments]
    
    classrooms = query.order_by(Classroom.name).all()
    return render_template('classroom/index.html', 
                         classrooms=classrooms,
                         departments=departments)

@classroom_bp.route('/admin')
@login_required
def admin_dashboard():
    if not (current_user.is_admin or current_user.is_teacher):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('classroom.index'))
    
    # If user is a teacher, only show classrooms for their department
    if current_user.is_teacher:
        classrooms = Classroom.query.filter_by(department=current_user.department).all()
    else:
        classrooms = Classroom.query.all()
    
    return render_template('classroom/admin_dashboard.html', classrooms=classrooms)

@classroom_bp.route('/<int:id>')
def show(id):
    try:
        classroom = Classroom.query.get_or_404(id)
        
        # Get current status
        now = datetime.now()
        current_day = now.strftime('%A')
        current_time = now.time()
        
        # Find current class
        current_entry = TimetableEntry.query.filter(
            TimetableEntry.classroom_id == id,
            TimetableEntry.day_of_week == current_day,
            TimetableEntry.start_time <= current_time,
            TimetableEntry.end_time >= current_time
        ).first()
        
        # Find next class
        next_entry = TimetableEntry.query.filter(
            TimetableEntry.classroom_id == id,
            TimetableEntry.day_of_week == current_day,
            TimetableEntry.start_time > current_time
        ).order_by(TimetableEntry.start_time).first()
        
        # Get all timetable entries for this classroom
        entries = TimetableEntry.query.filter_by(classroom_id=id).order_by(TimetableEntry.start_time).all()
        
        # Group entries by time slot
        timetable_grid = {}
        for entry in entries:
            time_slot = f"{entry.start_time.strftime('%H:%M')} - {entry.end_time.strftime('%H:%M')}"
            if time_slot not in timetable_grid:
                timetable_grid[time_slot] = {
                    'Monday': [], 'Tuesday': [], 'Wednesday': [],
                    'Thursday': [], 'Friday': [], 'Saturday': []
                }
            timetable_grid[time_slot][entry.day_of_week].append({
                'subject': entry.subject,
                'faculty': entry.faculty,
                'batch': entry.batch
            })
        
        # Sort time slots
        timetable_grid = dict(sorted(timetable_grid.items()))
        
        return render_template('classroom/show.html',
                             classroom=classroom,
                             current_entry=current_entry,
                             next_entry=next_entry,
                             timetable_entries=timetable_grid)
    except Exception as e:
        flash(f'Error loading classroom data: {str(e)}', 'error')
        return redirect(url_for('classroom.index'))

@classroom_bp.route('/<int:id>/status')
def get_status(id):
    classroom = Classroom.query.get_or_404(id)
    now = datetime.now()
    current_day = now.strftime('%A')
    current_time = now.time()
    
    # Find current class
    current_entry = TimetableEntry.query.filter(
        TimetableEntry.classroom_id == id,
        TimetableEntry.day_of_week == current_day,
        TimetableEntry.start_time <= current_time,
        TimetableEntry.end_time >= current_time
    ).first()
    
    if current_entry:
        time_remaining = (current_entry.end_time - current_time).total_seconds() / 60
        return jsonify({
            'occupied': True,
            'subject': current_entry.subject,
            'faculty': current_entry.faculty,
            'time_remaining': f"{int(time_remaining)} minutes"
        })
    
    # Find next class
    next_entry = TimetableEntry.query.filter(
        TimetableEntry.classroom_id == id,
        TimetableEntry.day_of_week == current_day,
        TimetableEntry.start_time > current_time
    ).order_by(TimetableEntry.start_time).first()
    
    if next_entry:
        return jsonify({
            'occupied': False,
            'next_class': {
                'subject': next_entry.subject,
                'time': next_entry.start_time.strftime('%H:%M')
            }
        })
    
    return jsonify({
        'occupied': False,
        'next_class': None
    })

@classroom_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not (current_user.is_admin or current_user.is_teacher):
        return jsonify({
            'success': False,
            'message': 'You do not have permission to create classrooms.'
        }), 403
        
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['name', 'location', 'room_type', 'department']
            for field in required_fields:
                if not request.form.get(field):
                    return jsonify({
                        'success': False,
                        'message': f'{field.title()} is required.'
                    }), 400

            # Check if classroom name already exists
            if Classroom.query.filter_by(name=request.form['name']).first():
                return jsonify({
                    'success': False,
                    'message': 'A classroom with this name already exists.'
                }), 400

            # If user is a teacher, they can only create classrooms for their department
            if current_user.is_teacher and request.form['department'] != current_user.department:
                return jsonify({
                    'success': False,
                    'message': 'Teachers can only create classrooms for their own department.'
                }), 403

            classroom = Classroom(
                name=request.form['name'],
                location=request.form['location'],
                room_type=request.form['room_type'],
                department=request.form['department'],
                is_active=bool(request.form.get('is_active'))
            )
            
            db.session.add(classroom)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Classroom created successfully.'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error creating classroom: {str(e)}'
            }), 400
        
    # For GET request, return the create form template
    return render_template('classroom/create.html')

@classroom_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    classroom = Classroom.query.get_or_404(id)
    
    # Check if user has permission to edit this classroom
    if not current_user.is_admin and (not current_user.is_teacher or classroom.department != current_user.department):
        flash('You do not have permission to edit this classroom.', 'danger')
        return redirect(url_for('classroom.index'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['name', 'location', 'room_type', 'department']
            for field in required_fields:
                if not request.form.get(field):
                    return jsonify({
                        'success': False,
                        'message': f'{field.title()} is required.'
                    }), 400
            
            # If user is a teacher, they can only edit classrooms for their department
            if current_user.is_teacher and request.form['department'] != current_user.department:
                return jsonify({
                    'success': False,
                    'message': 'Teachers can only edit classrooms for their own department.'
                }), 403
            
            # Check if classroom name already exists (excluding current classroom)
            existing = Classroom.query.filter_by(name=request.form['name']).first()
            if existing and existing.id != id:
                return jsonify({
                    'success': False,
                    'message': 'A classroom with this name already exists.'
                }), 400
            
            classroom.name = request.form['name']
            classroom.location = request.form['location']
            classroom.room_type = request.form['room_type']
            classroom.department = request.form['department']
            classroom.is_active = bool(request.form.get('is_active'))
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Classroom updated successfully.'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    return render_template('classroom/edit.html', classroom=classroom)

@classroom_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(id):
    classroom = Classroom.query.get_or_404(id)
    
    # Check if user has permission to toggle this classroom's status
    if not current_user.is_admin and (not current_user.is_teacher or classroom.department != current_user.department):
        return jsonify({
            'success': False,
            'message': 'You do not have permission to toggle this classroom\'s status.'
        }), 403
    
    try:
        classroom.is_active = not classroom.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Classroom {"activated" if classroom.is_active else "deactivated"} successfully.',
            'is_active': classroom.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@classroom_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    classroom = Classroom.query.get_or_404(id)
    
    # Check if user has permission to delete this classroom
    if not current_user.is_admin and (not current_user.is_teacher or classroom.department != current_user.department):
        return jsonify({
            'success': False,
            'message': 'You do not have permission to delete this classroom.'
        }), 403
    
    try:
        db.session.delete(classroom)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Classroom deleted successfully.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@classroom_bp.route('/<int:id>/schedule')
@login_required
def get_schedule(id):
    try:
        classroom = Classroom.query.get_or_404(id)
        
        # Get all timetable entries for this classroom
        entries = TimetableEntry.query.filter_by(classroom_id=id).order_by(TimetableEntry.start_time).all()
        
        # Group entries by time slot
        schedule = {}
        for entry in entries:
            time_slot = f"{entry.start_time.strftime('%H:%M')} - {entry.end_time.strftime('%H:%M')}"
            if time_slot not in schedule:
                schedule[time_slot] = {
                    'time': time_slot,
                    'Monday': None, 'Tuesday': None, 'Wednesday': None,
                    'Thursday': None, 'Friday': None, 'Saturday': None
                }
            schedule[time_slot][entry.day_of_week] = {
                'subject': entry.subject,
                'faculty': entry.faculty
            }
        
        return jsonify({
            'success': True,
            'schedule': list(schedule.values())
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading schedule: {str(e)}'
        }), 400

@classroom_bp.route('/create-demo-data')
@login_required
def create_demo_data_route():
    if not current_user.is_admin:
        flash('You do not have permission to create demo data.', 'danger')
        return redirect(url_for('classroom.index'))
    
    create_demo_data()
    flash('Demo data created successfully.', 'success')
    return redirect(url_for('classroom.index')) 