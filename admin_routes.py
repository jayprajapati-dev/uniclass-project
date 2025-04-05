from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Department
from marketplace_forms import DepartmentForm
from functools import wraps

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin/departments')
@login_required
@admin_required
def departments():
    departments = Department.query.order_by(Department.code).all()
    return render_template('admin/departments.html', departments=departments)

@admin.route('/admin/departments/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        department = Department(
            code=form.code.data.upper(),
            name=form.name.data,
            description=form.description.data,
            is_active=form.is_active.data
        )
        db.session.add(department)
        db.session.commit()
        flash('Department created successfully!', 'success')
        return redirect(url_for('admin.departments'))
    return render_template('admin/department_form.html', form=form, title='Create Department')

@admin.route('/admin/departments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_department(id):
    department = Department.query.get_or_404(id)
    form = DepartmentForm(obj=department)
    if form.validate_on_submit():
        department.code = form.code.data.upper()
        department.name = form.name.data
        department.description = form.description.data
        department.is_active = form.is_active.data
        db.session.commit()
        flash('Department updated successfully!', 'success')
        return redirect(url_for('admin.departments'))
    return render_template('admin/department_form.html', form=form, title='Edit Department')

@admin.route('/admin/departments/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_department(id):
    department = Department.query.get_or_404(id)
    if department.subjects or department.listings:
        flash('Cannot delete department with associated subjects or listings!', 'error')
    else:
        db.session.delete(department)
        db.session.commit()
        flash('Department deleted successfully!', 'success')
    return redirect(url_for('admin.departments')) 