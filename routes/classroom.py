from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Classroom, TimetableEntry
from datetime import datetime, timedelta
from sqlalchemy import distinct
from forms import ClassroomSearchForm, ClassroomForm

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
                    day=day,
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
    form = ClassroomSearchForm()
    query = Classroom.query.filter_by(is_active=True)

    # Apply filters from form
    if form.validate_on_submit():
        if form.search_query.data:
            search = f"%{form.search_query.data}%"
            query = query.filter(
                (Classroom.room_number.ilike(search)) |
                (Classroom.building.ilike(search)) |
                (Classroom.location.ilike(search))
            )
        
        if form.room_type.data:
            query = query.filter_by(room_type=form.room_type.data)
        if form.department.data:
            query = query.filter_by(department=form.department.data)
        if form.floor.data:
            query = query.filter_by(floor=form.floor.data)

    classrooms = query.order_by(Classroom.building, Classroom.floor, Classroom.room_number).all()
    return render_template('classrooms/index.html', classrooms=classrooms, form=form)

@classroom_bp.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('classroom.index'))
    
    form = ClassroomSearchForm()
    query = Classroom.query

    # Apply filters from form
    if form.validate_on_submit():
        if form.search_query.data:
            search = f"%{form.search_query.data}%"
            query = query.filter(
                (Classroom.room_number.ilike(search)) |
                (Classroom.building.ilike(search)) |
                (Classroom.location.ilike(search))
            )
        
        if form.room_type.data:
            query = query.filter_by(room_type=form.room_type.data)
        if form.department.data:
            query = query.filter_by(department=form.department.data)
        if form.floor.data:
            query = query.filter_by(floor=form.floor.data)

    classrooms = query.order_by(Classroom.building, Classroom.floor, Classroom.room_number).all()
    return render_template('classrooms/admin.html', classrooms=classrooms, form=form)

@classroom_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_admin:
        flash('You do not have permission to create classrooms.', 'danger')
        return redirect(url_for('classroom.index'))
        
    form = ClassroomForm()
    if form.validate_on_submit():
        try:
            # Check if classroom number already exists
            if Classroom.query.filter_by(room_number=form.room_number.data).first():
                flash('A classroom with this room number already exists.', 'danger')
                return render_template('classrooms/create.html', form=form)

            classroom = Classroom(
                room_number=form.room_number.data,
                location=form.location.data,
                room_type=form.room_type.data,
                department=form.department.data,
                floor=form.floor.data,
                building=form.building.data,
                is_active=True
            )
            
            db.session.add(classroom)
            db.session.commit()
            
            flash('Classroom created successfully.', 'success')
            return redirect(url_for('classroom.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating classroom: {str(e)}', 'danger')
            return render_template('classrooms/create.html', form=form)
        
    return render_template('classrooms/create.html', form=form)

@classroom_bp.route('/<int:id>')
def show(id):
    classroom = Classroom.query.get_or_404(id)
    return render_template('classrooms/show.html', classroom=classroom)

@classroom_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not current_user.is_admin:
        flash('You do not have permission to edit classrooms.', 'danger')
        return redirect(url_for('classroom.index'))
        
    classroom = Classroom.query.get_or_404(id)
    form = ClassroomForm(obj=classroom)
    
    if form.validate_on_submit():
        try:
            # Check if the new room number already exists (excluding current classroom)
            existing = Classroom.query.filter(
                Classroom.room_number == form.room_number.data,
                Classroom.id != id
            ).first()
            
            if existing:
                flash('A classroom with this room number already exists.', 'danger')
                return render_template('classrooms/edit.html', form=form, classroom=classroom)

            classroom.room_number = form.room_number.data
            classroom.location = form.location.data
            classroom.room_type = form.room_type.data
            classroom.department = form.department.data
            classroom.floor = form.floor.data
            classroom.building = form.building.data
            
            db.session.commit()
            flash('Classroom updated successfully.', 'success')
            return redirect(url_for('classroom.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating classroom: {str(e)}', 'danger')
            return render_template('classrooms/edit.html', form=form, classroom=classroom)
    
    return render_template('classrooms/edit.html', form=form, classroom=classroom)

@classroom_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'You do not have permission to delete classrooms.'}), 403
        
    try:
        classroom = Classroom.query.get_or_404(id)
        db.session.delete(classroom)
        db.session.commit()
        flash('Classroom deleted successfully.', 'success')
        return jsonify({
            'success': True,
            'message': 'Classroom deleted successfully.'
        })
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting classroom: {str(e)}', 'danger')
        return jsonify({
            'success': False,
            'message': f'Error deleting classroom: {str(e)}'
        }), 500

@classroom_bp.route('/<int:id>/status')
def get_status(id):
    classroom = Classroom.query.get_or_404(id)
    now = datetime.now()
    current_day = now.strftime('%A')
    current_time = now.time()
    
    # Find current class
    current_entry = TimetableEntry.query.filter(
        TimetableEntry.classroom_id == id,
        TimetableEntry.day == current_day,
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
        TimetableEntry.day == current_day,
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
            schedule[time_slot][entry.day] = {
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