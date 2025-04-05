from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Department, db
from forms import DepartmentForm
from functools import wraps

bp = Blueprint('department', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_administrator:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/departments')
@login_required
@admin_required
def list_departments():
    departments = Department.query.all()
    return render_template('admin/departments/list.html', departments=departments)

@bp.route('/departments/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        department = Department(
            name=form.name.data,
            code=form.code.data,
            description=form.description.data,
            is_active=form.is_active.data
        )
        db.session.add(department)
        try:
            db.session.commit()
            flash('Department added successfully!', 'success')
            return redirect(url_for('department.list_departments'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding department. Please try again.', 'error')
    return render_template('admin/departments/add.html', form=form)

@bp.route('/departments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_department(id):
    department = Department.query.get_or_404(id)
    form = DepartmentForm(obj=department)
    if form.validate_on_submit():
        department.name = form.name.data
        department.code = form.code.data
        department.description = form.description.data
        department.is_active = form.is_active.data
        try:
            db.session.commit()
            flash('Department updated successfully!', 'success')
            return redirect(url_for('department.list_departments'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating department. Please try again.', 'error')
    return render_template('admin/departments/edit.html', form=form, department=department)

@bp.route('/departments/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_department(id):
    department = Department.query.get_or_404(id)
    try:
        db.session.delete(department)
        db.session.commit()
        flash('Department deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting department. Please try again.', 'error')
    return redirect(url_for('department.list_departments')) 