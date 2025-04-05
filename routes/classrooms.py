from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, Classroom
from forms import ClassroomForm, ClassroomSearchForm

classrooms_bp = Blueprint('classrooms', __name__)

@classrooms_bp.route('/')
def index():
    form = ClassroomSearchForm()
    query = Classroom.query.filter_by(is_active=True)

    if form.validate_on_submit():
        if form.search_query.data:
            search = f"%{form.search_query.data}%"
            query = query.filter(
                (Classroom.name.ilike(search)) |
                (Classroom.building.ilike(search)) |
                (Classroom.location.ilike(search))
            )
        
        if form.room_type.data:
            query = query.filter_by(room_type=form.room_type.data)
        if form.department.data:
            query = query.filter_by(department=form.department.data)
        if form.building.data:
            query = query.filter_by(building=form.building.data)
        if form.floor.data:
            query = query.filter_by(floor=form.floor.data)

    classrooms = query.order_by(Classroom.building, Classroom.floor, Classroom.name).all()
    return render_template('classrooms/index.html', classrooms=classrooms, form=form)

@classrooms_bp.route('/<int:id>')
def view(id):
    classroom = Classroom.query.get_or_404(id)
    return render_template('classrooms/view.html', classroom=classroom)

# Admin routes for managing classrooms
@classrooms_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('classrooms.index'))
    
    classrooms = Classroom.query.order_by(Classroom.building, Classroom.floor, Classroom.name).all()
    return render_template('classrooms/admin.html', classrooms=classrooms)

@classrooms_bp.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('classrooms.index'))
    
    form = ClassroomForm()
    if form.validate_on_submit():
        classroom = Classroom(
            name=form.name.data,
            location=form.location.data,
            floor=form.floor.data,
            building=form.building.data,
            room_type=form.room_type.data,
            department=form.department.data
        )
        db.session.add(classroom)
        db.session.commit()
        flash('Classroom added successfully.', 'success')
        return redirect(url_for('classrooms.admin'))
    
    return render_template('classrooms/add.html', form=form)

@classrooms_bp.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('classrooms.index'))
    
    classroom = Classroom.query.get_or_404(id)
    form = ClassroomForm(obj=classroom)
    
    if form.validate_on_submit():
        classroom.name = form.name.data
        classroom.location = form.location.data
        classroom.floor = form.floor.data
        classroom.building = form.building.data
        classroom.room_type = form.room_type.data
        classroom.department = form.department.data
        db.session.commit()
        flash('Classroom updated successfully.', 'success')
        return redirect(url_for('classrooms.admin'))
    
    return render_template('classrooms/edit.html', form=form, classroom=classroom)

@classrooms_bp.route('/admin/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    classroom = Classroom.query.get_or_404(id)
    classroom.is_active = False
    db.session.commit()
    
    flash('Classroom deactivated successfully.', 'success')
    return redirect(url_for('classrooms.admin')) 