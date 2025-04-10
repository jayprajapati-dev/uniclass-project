from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from models import db, Timetable, TimeSlot, Subject, User, TimetableEntry, Classroom
from datetime import datetime, time
from utils.timetable_generator import TimetableGenerator
from sqlalchemy import distinct
from forms import TimetableForm

timetable_bp = Blueprint('timetable', __name__)

def init_db():
    """Initialize the database tables"""
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        raise e

def create_demo_data():
    """Create demo data if none exists"""
    # Check if we already have data
    if TimeSlot.query.first() is not None:
        return

    # Create time slots
    time_slots = [
        ('10:30', '11:30'),
        ('11:30', '12:30'),
        ('12:30', '13:30'),
        ('13:30', '14:30'),
        ('14:30', '15:30'),
        ('15:30', '16:30'),
        ('16:30', '17:30'),
        ('17:30', '18:00')
    ]

    for start_time, end_time in time_slots:
        slot = TimeSlot(
            start_time=datetime.strptime(start_time, '%H:%M').time(),
            end_time=datetime.strptime(end_time, '%H:%M').time()
        )
        db.session.add(slot)

    # Create demo classrooms
    classrooms = [
        ('101', 'Block A, Ground Floor', 'Ground', 'Block A', 'lecture_room', 'CE'),
        ('102', 'Block A, Ground Floor', 'Ground', 'Block A', 'lecture_room', 'EE'),
        ('103', 'Block A, Ground Floor', 'Ground', 'Block A', 'lecture_room', 'EC'),
        ('104', 'Block A, Ground Floor', 'Ground', 'Block A', 'lecture_room', 'IT'),
        ('105', 'Block A, Ground Floor', 'Ground', 'Block A', 'lecture_room', 'ICT'),
        ('106', 'Block A, Ground Floor', 'Ground', 'Block A', 'lecture_room', 'ME'),
        ('201', 'Block A, First Floor', 'First', 'Block A', 'lecture_room', 'CE'),
        ('202', 'Block A, First Floor', 'First', 'Block A', 'lecture_room', 'EE'),
        ('203', 'Block A, First Floor', 'First', 'Block A', 'lecture_room', 'EC'),
        ('204', 'Block A, First Floor', 'First', 'Block A', 'lecture_room', 'IT'),
        ('205', 'Block A, First Floor', 'First', 'Block A', 'lecture_room', 'ICT'),
        ('206', 'Block A, First Floor', 'First', 'Block A', 'lecture_room', 'ME'),
        ('301', 'Block A, Second Floor', 'Second', 'Block A', 'lecture_room', 'CE'),
        ('302', 'Block A, Second Floor', 'Second', 'Block A', 'lecture_room', 'EE'),
        ('303', 'Block A, Second Floor', 'Second', 'Block A', 'lecture_room', 'EC'),
        ('304', 'Block A, Second Floor', 'Second', 'Block A', 'lecture_room', 'IT'),
        ('305', 'Block A, Second Floor', 'Second', 'Block A', 'lecture_room', 'ICT'),
        ('306', 'Block A, Second Floor', 'Second', 'Block A', 'lecture_room', 'ME'),
        ('401', 'Block A, Third Floor', 'Third', 'Block A', 'lecture_room', 'CE'),
        ('402', 'Block A, Third Floor', 'Third', 'Block A', 'lecture_room', 'EE'),
        ('403', 'Block A, Third Floor', 'Third', 'Block A', 'lecture_room', 'EC'),
        ('404', 'Block A, Third Floor', 'Third', 'Block A', 'lecture_room', 'IT'),
        ('405', 'Block A, Third Floor', 'Third', 'Block A', 'lecture_room', 'ICT'),
        ('406', 'Block A, Third Floor', 'Third', 'Block A', 'lecture_room', 'ME'),
        ('501', 'Block A, Fourth Floor', 'Fourth', 'Block A', 'lecture_room', 'CE'),
        ('502', 'Block A, Fourth Floor', 'Fourth', 'Block A', 'lecture_room', 'EE'),
        ('503', 'Block A, Fourth Floor', 'Fourth', 'Block A', 'lecture_room', 'EC'),
        ('504', 'Block A, Fourth Floor', 'Fourth', 'Block A', 'lecture_room', 'IT'),
        ('505', 'Block A, Fourth Floor', 'Fourth', 'Block A', 'lecture_room', 'ICT'),
        ('506', 'Block A, Fourth Floor', 'Fourth', 'Block A', 'lecture_room', 'ME'),
        ('601', 'Block A, Fifth Floor', 'Fifth', 'Block A', 'lecture_room', 'CE'),
        ('602', 'Block A, Fifth Floor', 'Fifth', 'Block A', 'lecture_room', 'EE'),
        ('603', 'Block A, Fifth Floor', 'Fifth', 'Block A', 'lecture_room', 'EC'),
        ('604', 'Block A, Fifth Floor', 'Fifth', 'Block A', 'lecture_room', 'IT'),
        ('605', 'Block A, Fifth Floor', 'Fifth', 'Block A', 'lecture_room', 'ICT'),
        ('606', 'Block A, Fifth Floor', 'Fifth', 'Block A', 'lecture_room', 'ME')
    ]

    for name, location, floor, building, room_type, department in classrooms:
        classroom = Classroom(
            name=name,
            location=location,
            floor=floor,
            building=building,
            room_type=room_type,
            department=department
        )
        db.session.add(classroom)

    # Create subjects for each department and semester
    departments = ['CE', 'EE', 'EC', 'IT', 'ICT', 'ME']
    subjects_data = {
        'CE': {
            1: [
                ('Engineering Mathematics', 'CE Semester 1'),
                ('Engineering Physics', 'CE Semester 1'),
                ('Engineering Chemistry', 'CE Semester 1'),
                ('Basic Civil Engineering', 'CE Semester 1'),
                ('Engineering Mechanics', 'CE Semester 1')
            ],
            2: [
                ('Structural Analysis', 'CE Semester 2'),
                ('Building Materials', 'CE Semester 2'),
                ('Surveying', 'CE Semester 2'),
                ('Fluid Mechanics', 'CE Semester 2'),
                ('Construction Technology', 'CE Semester 2')
            ]
        },
        'EE': {
            1: [
                ('Engineering Mathematics', 'EE Semester 1'),
                ('Engineering Physics', 'EE Semester 1'),
                ('Basic Electrical Engineering', 'EE Semester 1'),
                ('Circuit Theory', 'EE Semester 1'),
                ('Electronics', 'EE Semester 1')
            ],
            2: [
                ('Power Systems', 'EE Semester 2'),
                ('Control Systems', 'EE Semester 2'),
                ('Electrical Machines', 'EE Semester 2'),
                ('Digital Electronics', 'EE Semester 2'),
                ('Power Electronics', 'EE Semester 2')
            ]
        },
        'EC': {
            1: [
                ('Engineering Mathematics', 'EC Semester 1'),
                ('Engineering Physics', 'EC Semester 1'),
                ('Basic Electronics', 'EC Semester 1'),
                ('Circuit Theory', 'EC Semester 1'),
                ('Digital Logic', 'EC Semester 1')
            ],
            2: [
                ('Analog Electronics', 'EC Semester 2'),
                ('Digital Electronics', 'EC Semester 2'),
                ('Communication Systems', 'EC Semester 2'),
                ('Signals and Systems', 'EC Semester 2'),
                ('Microprocessors', 'EC Semester 2')
            ]
        },
        'IT': {
            1: [
                ('Engineering Mathematics', 'IT Semester 1'),
                ('Programming Fundamentals', 'IT Semester 1'),
                ('Data Structures', 'IT Semester 1'),
                ('Computer Organization', 'IT Semester 1'),
                ('Database Systems', 'IT Semester 1')
            ],
            2: [
                ('Web Development', 'IT Semester 2'),
                ('Computer Networks', 'IT Semester 2'),
                ('Software Engineering', 'IT Semester 2'),
                ('Operating Systems', 'IT Semester 2'),
                ('Cloud Computing', 'IT Semester 2')
            ]
        },
        'ICT': {
            1: [
                ('Engineering Mathematics', 'ICT Semester 1'),
                ('Programming Fundamentals', 'ICT Semester 1'),
                ('Data Structures', 'ICT Semester 1'),
                ('Computer Organization', 'ICT Semester 1'),
                ('Database Systems', 'ICT Semester 1')
            ],
            2: [
                ('Web Development', 'ICT Semester 2'),
                ('Computer Networks', 'ICT Semester 2'),
                ('Software Engineering', 'ICT Semester 2'),
                ('Operating Systems', 'ICT Semester 2'),
                ('Cloud Computing', 'ICT Semester 2')
            ]
        },
        'ME': {
            1: [
                ('Engineering Mathematics', 'ME Semester 1'),
                ('Engineering Physics', 'ME Semester 1'),
                ('Engineering Mechanics', 'ME Semester 1'),
                ('Thermodynamics', 'ME Semester 1'),
                ('Manufacturing Processes', 'ME Semester 1')
            ],
            2: [
                ('Machine Design', 'ME Semester 2'),
                ('Heat Transfer', 'ME Semester 2'),
                ('Fluid Mechanics', 'ME Semester 2'),
                ('Production Technology', 'ME Semester 2'),
                ('Industrial Engineering', 'ME Semester 2')
            ]
        }
    }

    for dept in departments:
        for sem in range(1, 7):
            if sem in subjects_data[dept]:
                for subject_name, batch in subjects_data[dept][sem]:
                    subject = Subject(
                        name=subject_name,
                        batch=batch,
                        department=dept,
                        semester=sem
                    )
                    db.session.add(subject)

    # Create timetable entries
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    time_slots = TimeSlot.query.all()
    subjects = Subject.query.all()
    classrooms = Classroom.query.all()

    # Create a default timetable
    # First, try to find an admin user
    admin_user = User.query.filter_by(role='admin').first()
    if not admin_user:
        # If no admin user exists, create one
        admin_user = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            department='Administration',
            is_admin=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.flush()

    timetable = Timetable(
        title='Default Timetable',
        semester='2024-25',
        department='All',
        created_by=admin_user.id,
        start_date=datetime.now()
    )
    db.session.add(timetable)
    db.session.flush()  # Get the timetable ID

    for slot in time_slots:
        for day in days:
            for subject in subjects:
                # Find a classroom for this subject's department
                classroom = next((c for c in classrooms if c.department == subject.department), None)
                if classroom:
                    entry = TimetableEntry(
                        timetable_id=timetable.id,
                        day=day,
                        time_slot_id=slot.id,
                        subject_id=subject.id,
                        classroom_id=classroom.id
                    )
                    db.session.add(entry)

    db.session.commit()

@timetable_bp.route('/')
def index():
    form = TimetableForm()
    # Get filter parameters
    department = request.args.get('department', '')
    semester = request.args.get('semester', '')
    
    # Get all departments for the filter dropdown
    departments = [
        ('CE', 'Civil Engineering (CE)'),
        ('ME', 'Mechanical Engineering (ME)'),
        ('EE', 'Electrical Engineering (EE)'),
        ('EC', 'Electronics & Communication Engineering (EC)'),
        ('IT', 'Information Technology (IT)'),
        ('ICT', 'Information and Communication Technology (ICT)')
    ]
    
    # Get all semesters for the filter dropdown
    semesters = [
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6')
    ]
    
    # Get filtered timetable entries with time slot information
    query = TimetableEntry.query.join(Classroom).join(TimeSlot)
    if department:
        query = query.filter(Classroom.department.ilike(f'%{department}%'))
    if semester:
        query = query.filter(TimetableEntry.semester == semester)
    
    entries = query.order_by(TimeSlot.start_time).all()
    
    # Group entries by time slot
    timetable_grid = {}
    for entry in entries:
        time_slot = f"{entry.time_slot.start_time.strftime('%H:%M')} - {entry.time_slot.end_time.strftime('%H:%M')}"
        if time_slot not in timetable_grid:
            timetable_grid[time_slot] = {
                'Monday': [], 'Tuesday': [], 'Wednesday': [],
                'Thursday': [], 'Friday': [], 'Saturday': []
            }
        timetable_grid[time_slot][entry.day].append({
            'subject': entry.subject,
            'faculty': entry.faculty,
            'batch': entry.batch,
            'classroom': entry.classroom.name
        })
    
    # Sort time slots
    timetable_grid = dict(sorted(timetable_grid.items()))
    
    return render_template('timetable/index.html',
                         timetable_entries=timetable_grid,
                         departments=departments,
                         semesters=semesters,
                         selected_department=department,
                         selected_semester=semester,
                         form=form)

@timetable_bp.route('/<int:id>')
def show(id):
    try:
        timetable = TimetableEntry.query.get_or_404(id)
        
        # Get all timetable entries for this classroom
        entries = TimetableEntry.query.filter_by(classroom_id=timetable.classroom_id).order_by(TimetableEntry.start_time).all()
        
        # Group entries by time slot
        timetable_grid = {}
        for entry in entries:
            time_slot = f"{entry.start_time.strftime('%H:%M')} - {entry.end_time.strftime('%H:%M')}"
            if time_slot not in timetable_grid:
                timetable_grid[time_slot] = {
                    'Monday': [], 'Tuesday': [], 'Wednesday': [],
                    'Thursday': [], 'Friday': [], 'Saturday': []
                }
            timetable_grid[time_slot][entry.day].append({
                'subject': entry.subject,
                'faculty': entry.faculty,
                'batch': entry.batch
            })
        
        # Sort time slots
        timetable_grid = dict(sorted(timetable_grid.items()))
        
        return render_template('timetable/show.html',
                             timetable=timetable,
                             timetable_entries=timetable_grid)
    except Exception as e:
        flash(f'Error loading timetable data: {str(e)}', 'error')
        return redirect(url_for('timetable.index'))

# Admin routes for managing timetables
@timetable_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('timetable.index'))
    
    entries = TimetableEntry.query.order_by(TimetableEntry.start_time).all()
    return render_template('timetable/admin.html', entries=entries)

@timetable_bp.route('/admin/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('timetable.index'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['classroom_id', 'day', 'start_time', 'end_time', 'subject', 'faculty', 'batch']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field.title()} is required.', 'danger')
                    return redirect(url_for('timetable.create'))
            
            entry = TimetableEntry(
                classroom_id=request.form['classroom_id'],
                day=request.form['day'],
                start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
                end_time=datetime.strptime(request.form['end_time'], '%H:%M').time(),
                subject=request.form['subject'],
                faculty=request.form['faculty'],
                batch=request.form['batch']
            )
            
            db.session.add(entry)
            db.session.commit()
            
            flash('Timetable entry created successfully.', 'success')
            return redirect(url_for('timetable.admin'))
        except Exception as e:
            flash(f'Error creating timetable entry: {str(e)}', 'danger')
            return redirect(url_for('timetable.create'))
    
    # For GET request, return the create form template
    classrooms = Classroom.query.filter_by(is_active=True).all()
    return render_template('timetable/create.html', classrooms=classrooms)

@timetable_bp.route('/admin/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_admin(id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('timetable.index'))
    
    entry = TimetableEntry.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['classroom_id', 'day', 'time_slot_id', 'subject', 'faculty', 'batch']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field.title()} is required.', 'danger')
                    return redirect(url_for('timetable.edit_admin', id=id))
            
            entry.classroom_id = request.form['classroom_id']
            entry.day = request.form['day']
            entry.time_slot_id = request.form['time_slot_id']
            entry.subject = request.form['subject']
            entry.faculty = request.form['faculty']
            entry.batch = request.form['batch']
            
            db.session.commit()
            
            flash('Timetable entry updated successfully.', 'success')
            return redirect(url_for('timetable.admin'))
        except Exception as e:
            flash(f'Error updating timetable entry: {str(e)}', 'danger')
            return redirect(url_for('timetable.edit_admin', id=id))
    
    # For GET request, return the edit form template
    classrooms = Classroom.query.filter_by(is_active=True).all()
    time_slots = TimeSlot.query.all()
    return render_template('timetable/edit.html', entry=entry, classrooms=classrooms, time_slots=time_slots)

@timetable_bp.route('/admin/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('timetable.index'))
    
    entry = TimetableEntry.query.get_or_404(id)
    
    try:
        db.session.delete(entry)
        db.session.commit()
        flash('Timetable entry deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting timetable entry: {str(e)}', 'danger')
    
    return redirect(url_for('timetable.admin'))

@timetable_bp.route('/create', methods=['POST'])
@login_required
def create_timetable():
    """Create a new empty timetable"""
    if not current_user.is_teacher and not current_user.is_administrator:
        flash('Only teachers can create timetables.', 'error')
        return redirect(url_for('timetable.index'))

    branch = request.form.get('branch')
    semester = int(request.form.get('semester'))
    classroom_name = request.form.get('classroom')
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')

    # Map branch codes to full names
    branch_names = {
        'CE': 'Civil Engineering',
        'ME': 'Mechanical Engineering',
        'EE': 'Electrical Engineering',
        'EC': 'Electronics & Communication',
        'IT': 'Information Technology',
        'CH': 'Chemical Engineering',
        'IC': 'Instrumentation & Control'
    }
    
    # Get full branch name
    full_branch_name = branch_names.get(branch, branch)

    classroom = Classroom.query.filter_by(room_number=classroom_name).first()
    if not classroom:
        # Create new classroom
        classroom = Classroom(
            room_number=classroom_name,
            location=f'Building {classroom_name[0]}',  # Assume first character is building
            floor='1',  # Default floor
            building=f'Building {classroom_name[0]}',
            room_type='lecture_room',  # Default type
            department=full_branch_name
        )
        db.session.add(classroom)
        db.session.flush()

    # Create new empty timetable
    timetable = Timetable(
        title=f"Government Polytechnic Palanpur - {full_branch_name} Department",
        semester=str(semester),
        department=full_branch_name,
        created_by=current_user.id,
        start_date=start_date
    )
    db.session.add(timetable)
    db.session.commit()

    flash('Empty timetable created successfully! Please add entries manually.', 'success')
    return redirect(url_for('timetable.edit', id=timetable.id))

@timetable_bp.route('/view/<int:id>')
@login_required
def view(id):
    """View a specific timetable"""
    timetable = Timetable.query.get_or_404(id)
    entries = TimetableEntry.query.filter_by(timetable_id=id).all()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Fixed time slots
    time_slots = [
        {'start_time': '10:30 AM', 'end_time': '11:30 AM', 'type': 'class'},
        {'start_time': '11:30 AM', 'end_time': '12:30 PM', 'type': 'class'},
        {'start_time': '12:30 PM', 'end_time': '01:30 PM', 'type': 'recess', 'label': 'Recess Time'},
        {'start_time': '01:30 PM', 'end_time': '02:30 PM', 'type': 'class'},
        {'start_time': '02:30 PM', 'end_time': '03:30 PM', 'type': 'class'},
        {'start_time': '03:30 PM', 'end_time': '04:00 PM', 'type': 'class'},
        {'start_time': '04:00 PM', 'end_time': '04:10 PM', 'type': 'break', 'label': 'Break Time'},
        {'start_time': '04:10 PM', 'end_time': '05:10 PM', 'type': 'class'},
        {'start_time': '05:10 PM', 'end_time': '06:10 PM', 'type': 'class'}
    ]
    
    # Organize entries by day and time slot
    schedule = {}
    for day in days:
        schedule[day] = {}
        for i in range(len(time_slots)):
            schedule[day][i] = '-'  # Default empty entry
            for entry in entries:
                if entry.day == day and entry.time_slot_id == i + 1:  # time_slot_id starts from 1
                    subject = Subject.query.get(entry.subject_id)
                    if subject:
                        schedule[day][i] = {
                            'id': f"{day}_{i}",
                            'subject_name': subject.name,
                            'teacher_name': entry.teacher_name if entry.teacher_name else '-',
                            'classroom': entry.classroom.name if entry.classroom else '-'
                        }
    
    # Calculate term end date (120 days from start)
    from datetime import timedelta
    end_date = timetable.start_date + timedelta(days=120)
    
    return render_template(
        'timetable/view.html',
        timetable=timetable,
        schedule=schedule,
        time_slots=time_slots,
        days=days,
        end_date=end_date
    )

@timetable_bp.route('/edit/<int:id>')
@login_required
def edit(id):
    """Edit a specific timetable"""
    timetable = Timetable.query.get_or_404(id)
    if not current_user.is_teacher and not current_user.is_administrator:
        flash('Only teachers can edit timetables.', 'error')
        return redirect(url_for('timetable.view', id=id))

    if timetable.created_by != current_user.id and not current_user.is_administrator:
        flash('You can only edit your own timetables.', 'error')
        return redirect(url_for('timetable.view', id=id))

    entries = TimetableEntry.query.filter_by(timetable_id=id).all()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    # Get all time slots
    time_slots = TimeSlot.query.all()
    
    # Organize entries by day and slot
    schedule = {}
    for day in days:
        schedule[day] = {}
        for time_slot in time_slots:
            schedule[day][time_slot.id] = '-'  # Default empty entry
            for entry in entries:
                if entry.day == day and entry.time_slot_id == time_slot.id:
                    # Skip if this is part of a lab's second slot
                    if entry.subject_type == 'lab' and time_slot.id > 1:
                        prev_entry = next((e for e in entries if e.day == day and 
                                         e.time_slot_id == time_slot.id - 1 and 
                                         e.subject_type == 'lab'), None)
                        if prev_entry:
                            continue
                    
                    schedule[day][time_slot.id] = {
                        'id': f"{day}_{time_slot.id}",
                        'subject_code': entry.subject_code or '-',
                        'subject_type': entry.subject_type,
                        'classroom': entry.classroom or '-',
                        'teacher_name': entry.teacher_name or '-'
                    }
    
    return render_template(
        'timetable/edit.html',
        timetable=timetable,
        schedule=schedule,
        days=days,
        time_slots=time_slots
    )

@timetable_bp.route('/manage')
@login_required
def manage():
    try:
        if not current_user.has_role('admin'):
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('timetable.index'))
        
        subjects = Subject.query.all()
        time_slots = TimeSlot.query.all()
        teachers = User.query.filter(User.roles.any(name='teacher')).all()
        
        return render_template('timetable/manage.html',
                            subjects=subjects,
                            time_slots=time_slots,
                            teachers=teachers)
    except Exception as e:
        flash(f'Error loading timetable management: {str(e)}', 'error')
        return redirect(url_for('timetable.index'))

@timetable_bp.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    if not current_user.has_role('admin'):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('timetable.manage'))
    
    name = request.form.get('name')
    code = request.form.get('code')
    room = request.form.get('room')
    teacher_id = request.form.get('teacher_id', type=int)
    semester = request.form.get('semester', type=int)
    department = request.form.get('department')
    
    subject = Subject(
        name=name,
        code=code,
        room=room,
        teacher_id=teacher_id,
        semester=semester,
        department=department
    )
    
    db.session.add(subject)
    db.session.commit()
    
    flash('Subject added successfully.', 'success')
    return redirect(url_for('timetable.manage'))

@timetable_bp.route('/add_timeslot', methods=['POST'])
@login_required
def add_timeslot():
    try:
        if not current_user.has_role('admin'):
            return jsonify({
                'success': False,
                'message': 'You do not have permission to perform this action.'
            }), 403
        
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        
        if not start_time or not end_time:
            return jsonify({
                'success': False,
                'message': 'Start time and end time are required.'
            }), 400
        
        # Check for overlapping time slots
        existing = TimeSlot.query.filter(
            ((TimeSlot.start_time <= start_time) & (TimeSlot.end_time > start_time)) |
            ((TimeSlot.start_time < end_time) & (TimeSlot.end_time >= end_time))
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'This time slot overlaps with an existing time slot.'
            }), 400
        
        timeslot = TimeSlot(
            start_time=datetime.strptime(start_time, '%H:%M').time(),
            end_time=datetime.strptime(end_time, '%H:%M').time()
        )
        
        db.session.add(timeslot)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Time slot added successfully.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error adding time slot: {str(e)}'
        }), 400

@timetable_bp.route('/add_entry/<int:id>', methods=['POST'])
@login_required
def add_entry(id):
    """Add or update a timetable entry"""
    if not current_user.is_teacher and not current_user.is_administrator:
        return jsonify({'success': False, 'message': 'Only teachers can edit timetables.'})

    timetable = Timetable.query.get_or_404(id)
    if timetable.created_by != current_user.id and not current_user.is_administrator:
        return jsonify({'success': False, 'message': 'You can only edit your own timetables.'})

    try:
        # Get form data
        cell_id = request.form.get('cell_id')  # Format: day_index
        subject_code = request.form.get('subject_code', '').strip()
        subject_type = request.form.get('subject_type', 'lecture')
        classroom = request.form.get('classroom', '').strip()
        teacher_name = request.form.get('teacher_name', '').strip()

        # Get slot index from cell_id (format: Monday_0, Tuesday_1, etc.)
        if not cell_id or '_' not in cell_id:
            return jsonify({
                'success': False,
                'message': 'Invalid cell ID format'
            })

        day, slot_index = cell_id.split('_')
        
        # Define time slots
        time_slots = [
            {'start_time': '10:30 AM', 'end_time': '11:30 AM', 'type': 'class'},
            {'start_time': '11:30 AM', 'end_time': '12:30 PM', 'type': 'class'},
            {'start_time': '01:00 PM', 'end_time': '02:00 PM', 'type': 'class'},
            {'start_time': '02:00 PM', 'end_time': '03:00 PM', 'type': 'class'},
            {'start_time': '03:00 PM', 'end_time': '04:00 PM', 'type': 'class'},
            {'start_time': '04:10 PM', 'end_time': '05:10 PM', 'type': 'class'},
            {'start_time': '05:10 PM', 'end_time': '06:10 PM', 'type': 'class'}
        ]

        try:
            slot_index = int(slot_index)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid slot index'
            })

        # Validate slot index
        if slot_index < 0 or slot_index >= len(time_slots):
            return jsonify({
                'success': False,
                'message': 'Invalid time slot'
            })
            
        # Validate time slot
        if slot_index >= len(time_slots):
            return jsonify({
                'success': False,
                'message': 'Invalid time slot'
            })

        # Delete existing entries for this slot
        TimetableEntry.query.filter_by(
            timetable_id=id,
            day_of_week=day,
            time_slot_index=slot_index
        ).delete()

        # If all fields are empty, leave the slot empty
        if not any([subject_code, classroom, teacher_name]):
            db.session.commit()
            return jsonify({
                'success': True,
                'data': {
                    'cell_id': cell_id,
                    'content': '-',
                    'is_empty': True
                }
            })

        # Create new entry with time slot data

        # For lab entries, check if next slot is available
        if subject_type == 'lab':
            next_slot = slot_index + 1
            if next_slot >= len(time_slots):
                return jsonify({
                    'success': False,
                    'message': 'Labs require two consecutive slots. Cannot add lab in last slot.'
                })

            # Delete existing entry in next slot
            TimetableEntry.query.filter_by(
                timetable_id=id,
                day_of_week=day,
                time_slot_index=next_slot
            ).delete()

        # Create entry data
        entry_data = {
            'timetable_id': id,
            'day_of_week': day,
            'time_slot_index': slot_index,
            'subject_code': subject_code or '-',
            'subject_type': subject_type,
            'classroom': classroom or '-',
            'teacher_name': teacher_name or '-',
            'start_time': time_slots[slot_index]['start_time'],
            'end_time': time_slots[slot_index]['end_time'],
            'type': time_slots[slot_index]['type'],
            'is_second_hour': False
        }
        new_entry = TimetableEntry(**entry_data)
        db.session.add(new_entry)

        # For lab entries, create second hour entry
        if subject_type == 'lab':
            second_hour_data = entry_data.copy()
            second_hour_data.update({
                'time_slot_index': next_slot,
                'start_time': time_slots[next_slot]['start_time'],
                'end_time': time_slots[next_slot]['end_time'],
                'is_second_hour': True
            })
            second_hour = TimetableEntry(**second_hour_data)
            db.session.add(second_hour)

        # For labs, handle the second slot
        spans_two_slots = False
        if subject_type == 'lab' and slot_index < 7:  # 7 is the last slot
            # Delete any existing entry in next slot
            TimetableEntry.query.filter_by(
                timetable_id=id,
                day_of_week=day,
                time_slot_index=slot_index + 1
            ).delete()
            # Create lab's second hour entry
            entry_data['time_slot_index'] = slot_index + 1
            next_entry = TimetableEntry(**entry_data)
            db.session.add(next_entry)
            spans_two_slots = True

        db.session.commit()
        return jsonify({
            'success': True,
            'data': {
                'cell_id': cell_id,
                'content': f"{subject_code}<br>{classroom}<br>{teacher_name}",
                'subject_type': subject_type,
                'spans_two_slots': spans_two_slots,
                'next_cell_id': f"{day}_{slot_index + 1}" if spans_two_slots else None
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error saving entry: {str(e)}'
        }), 400

@timetable_bp.route('/move_entry/<int:id>', methods=['POST'])
@login_required
def move_entry(id):
    if not current_user.is_teacher and not current_user.is_administrator:
        return jsonify({'success': False, 'message': 'Only teachers can edit timetables.'})

    data = request.get_json()
    entry_id = data.get('entry_id')
    target_day = data.get('target_day')
    target_slot = int(data.get('target_slot'))

    # Define time slots
    time_slots = [
        {'start_time': '10:30 AM', 'end_time': '11:30 AM', 'type': 'class'},
        {'start_time': '11:30 AM', 'end_time': '12:30 PM', 'type': 'class'},
        {'start_time': '01:00 PM', 'end_time': '02:00 PM', 'type': 'class'},
        {'start_time': '02:00 PM', 'end_time': '03:00 PM', 'type': 'class'},
        {'start_time': '03:00 PM', 'end_time': '04:00 PM', 'type': 'class'},
        {'start_time': '04:10 PM', 'end_time': '05:10 PM', 'type': 'class'},
        {'start_time': '05:10 PM', 'end_time': '06:10 PM', 'type': 'class'}
    ]

    # Get the entry to move
    entry = TimetableEntry.query.get_or_404(entry_id)
    if entry.timetable_id != id:
        return jsonify({'success': False, 'message': 'Invalid entry'})

    # If it's a lab entry, validate the next slot
    if entry.subject_type == 'lab':
        next_slot = target_slot + 1
        if next_slot >= len(time_slots):
            return jsonify({
                'success': False,
                'message': 'Labs require two consecutive slots. Cannot move lab to last slot.'
            })

        # Check if next slot is available
        next_entry = TimetableEntry.query.filter_by(
            timetable_id=id,
            day=target_day,
            time_slot_id=next_slot + 1  # time_slot_id starts from 1
        ).first()

        if next_entry and next_entry.id != entry.id:
            return jsonify({
                'success': False,
                'message': 'Labs require two consecutive slots. Next slot is occupied.'
            })

    # Update the entry's position
    entry.day = target_day
    entry.time_slot_id = target_slot + 1  # time_slot_id starts from 1

    # If it's a lab, move the second hour as well
    if entry.subject_type == 'lab':
        second_hour = TimetableEntry.query.filter_by(
            timetable_id=id,
            day=entry.day,
            time_slot_id=entry.time_slot_id + 1,
            subject_code=entry.subject_code
        ).first()

        if second_hour:
            second_hour.day = target_day
            second_hour.time_slot_id = target_slot + 2  # time_slot_id starts from 1

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@timetable_bp.route('/delete_entry/<int:id>', methods=['POST'])
@login_required
def delete_entry(id):
    try:
        if not current_user.has_role('admin'):
            return jsonify({
                'success': False,
                'message': 'You do not have permission to perform this action.'
            }), 403
        
        entry = TimetableEntry.query.get_or_404(id)
        db.session.delete(entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Timetable entry deleted successfully.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting timetable entry: {str(e)}'
        }), 400