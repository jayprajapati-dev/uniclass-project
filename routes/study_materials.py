from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, StudyMaterial, Subject, User
from werkzeug.utils import secure_filename
import os

study_materials_bp = Blueprint('study_materials', __name__)

@study_materials_bp.route('/')
@login_required
def list_materials():
    materials = StudyMaterial.query.all()
    return render_template('study_materials/list.html', materials=materials)

@study_materials_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_material():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        subject_id = request.form.get('subject_id')
        file = request.files.get('file')
        
        if not all([title, description, subject_id]):
            flash('All fields are required', 'error')
            return redirect(url_for('study_materials.create_material'))
        
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        
        material = StudyMaterial(
            title=title,
            description=description,
            subject_id=subject_id,
            file_path=filename,
            uploaded_by=current_user.id
        )
        
        db.session.add(material)
        db.session.commit()
        
        flash('Study material created successfully', 'success')
        return redirect(url_for('study_materials.list_materials'))
    
    subjects = Subject.query.all()
    return render_template('study_materials/create.html', subjects=subjects)

@study_materials_bp.route('/<int:id>')
@login_required
def view_material(id):
    material = StudyMaterial.query.get_or_404(id)
    return render_template('study_materials/view.html', material=material)

@study_materials_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_material(id):
    material = StudyMaterial.query.get_or_404(id)
    
    if request.method == 'POST':
        material.title = request.form.get('title')
        material.description = request.form.get('description')
        material.subject_id = request.form.get('subject_id')
        
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            # Delete old file if exists
            if material.file_path:
                old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.file_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            material.file_path = filename
        
        db.session.commit()
        flash('Study material updated successfully', 'success')
        return redirect(url_for('study_materials.view_material', id=material.id))
    
    subjects = Subject.query.all()
    return render_template('study_materials/edit.html', material=material, subjects=subjects)

@study_materials_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_material(id):
    material = StudyMaterial.query.get_or_404(id)
    
    # Delete file if exists
    if material.file_path:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.session.delete(material)
    db.session.commit()
    
    flash('Study material deleted successfully', 'success')
    return redirect(url_for('study_materials.list_materials'))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 