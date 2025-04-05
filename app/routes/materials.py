from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
from models import db, Material, Department, Subject
from forms.materials import MaterialForm
import os
from werkzeug.utils import secure_filename

materials = Blueprint('materials', __name__)

@materials.route('/')
def index():
    # Get filter parameters
    query = request.args.get('query', '')
    department = request.args.get('department', 'all')
    semester = request.args.get('semester', 'all')
    subject = request.args.get('subject', 'all')
    material_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    materials_query = Material.query
    
    if query:
        materials_query = materials_query.filter(
            (Material.title.ilike(f'%{query}%')) |
            (Material.description.ilike(f'%{query}%'))
        )
    
    if department != 'all':
        materials_query = materials_query.filter(Material.department_id == department)
    
    if semester != 'all':
        materials_query = materials_query.filter(Material.semester == semester)
    
    if subject != 'all':
        materials_query = materials_query.filter(Material.subject_id == subject)
    
    if material_type != 'all':
        materials_query = materials_query.filter(Material.type == material_type)
    
    # Get paginated results
    materials = materials_query.order_by(Material.upload_date.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Get departments and subjects for filters
    departments = Department.query.filter_by(status='active').all()
    available_subjects = Subject.query.all()
    
    return render_template(
        'materials/index.html',
        materials=materials,
        departments=departments,
        available_subjects=available_subjects
    )

@materials.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = MaterialForm()
    
    # Populate department choices
    form.department.choices = [(d.id, d.name) for d in Department.query.filter_by(status='active').all()]
    
    # Populate semester choices
    form.semester.choices = [(i, f'Semester {i}') for i in range(1, 9)]
    
    # Populate subject choices
    form.subject.choices = [(s.id, s.name) for s in Subject.query.all()]
    
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'materials')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Create material record
        material = Material(
            title=form.title.data,
            department_id=form.department.data,
            semester=form.semester.data,
            subject_id=form.subject.data,
            type=form.type.data,
            file_path=file_path,
            description=form.description.data,
            uploaded_by_id=current_user.id
        )
        
        db.session.add(material)
        db.session.commit()
        
        flash('Material uploaded successfully!', 'success')
        return redirect(url_for('materials.index'))
    
    return render_template('materials/upload.html', form=form)

@materials.route('/download/<int:id>')
@login_required
def download(id):
    material = Material.query.get_or_404(id)
    return send_file(
        material.file_path,
        as_attachment=True,
        download_name=os.path.basename(material.file_path)
    )

@materials.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    material = Material.query.get_or_404(id)
    
    # Check if user has permission to delete
    if current_user.id != material.uploaded_by_id and not current_user.is_admin:
        flash('You do not have permission to delete this material.', 'error')
        return redirect(url_for('materials.index'))
    
    try:
        # Delete file
        if os.path.exists(material.file_path):
            os.remove(material.file_path)
        
        # Delete record
        db.session.delete(material)
        db.session.commit()
        
        flash('Material deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting material.', 'error')
    
    return redirect(url_for('materials.index')) 