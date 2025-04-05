from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, StudyMaterial, MaterialPurchase, MaterialReport, Message
from forms import StudyMaterialForm, MaterialSearchForm, MaterialReportForm
from flask_wtf import FlaskForm
import os
from datetime import datetime
from sqlalchemy import or_, and_

materials_bp = Blueprint('materials', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@materials_bp.route('/')
def index():
    form = MaterialSearchForm()
    query = StudyMaterial.query.filter_by(status='approved')

    if form.validate_on_submit():
        if form.search_query.data:
            search = f"%{form.search_query.data}%"
            query = query.filter(or_(
                StudyMaterial.title.ilike(search),
                StudyMaterial.description.ilike(search),
                StudyMaterial.subject.ilike(search)
            ))
        
        if form.material_type.data:
            query = query.filter_by(material_type=form.material_type.data)
        if form.branch.data:
            query = query.filter_by(branch=form.branch.data)
        if form.semester.data:
            query = query.filter_by(semester=form.semester.data)
        if form.condition.data:
            query = query.filter_by(condition=form.condition.data)
        if form.min_price.data is not None:
            query = query.filter(StudyMaterial.price >= form.min_price.data)
        if form.max_price.data is not None:
            query = query.filter(StudyMaterial.price <= form.max_price.data)

    materials = query.order_by(StudyMaterial.created_at.desc()).all()
    return render_template('materials/index.html', materials=materials, form=form)

@materials_bp.route('/list', methods=['GET', 'POST'])
@login_required
def list_material():
    form = StudyMaterialForm()
    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            file = form.image.data
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'materials', filename)
                file.save(filepath)
                image_path = f'materials/{filename}'
            else:
                flash('Invalid file type. Please upload a JPG or PNG image.', 'danger')
                return render_template('materials/list.html', form=form)

        material = StudyMaterial(
            title=form.title.data,
            subject=form.subject.data,
            material_type=form.material_type.data,
            branch=form.branch.data,
            semester=form.semester.data,
            price=form.price.data,
            condition=form.condition.data,
            description=form.description.data,
            image_path=image_path,
            seller_id=current_user.id
        )
        db.session.add(material)
        db.session.commit()

        flash('Your material has been listed and is pending approval.', 'success')
        return redirect(url_for('materials.index'))

    return render_template('materials/list.html', form=form)

@materials_bp.route('/<int:id>')
def view(id):
    material = StudyMaterial.query.get_or_404(id)
    report_form = MaterialReportForm()
    return render_template('materials/view.html', material=material, report_form=report_form)

@materials_bp.route('/<int:id>/contact', methods=['POST'])
@login_required
def contact_seller(id):
    material = StudyMaterial.query.get_or_404(id)
    if material.seller_id == current_user.id:
        flash('You cannot contact yourself.', 'danger')
        return redirect(url_for('materials.view', id=id))

    message = Message(
        sender_id=current_user.id,
        receiver_id=material.seller_id,
        content=request.form.get('message'),
        message_type='text'
    )
    db.session.add(message)
    db.session.commit()

    flash('Message sent to seller.', 'success')
    return redirect(url_for('materials.view', id=id))

@materials_bp.route('/<int:id>/report', methods=['POST'])
@login_required
def report_material(id):
    material = StudyMaterial.query.get_or_404(id)
    form = MaterialReportForm()
    
    if form.validate_on_submit():
        report = MaterialReport(
            material_id=id,
            reporter_id=current_user.id,
            report_type=form.report_type.data,
            description=form.description.data
        )
        db.session.add(report)
        db.session.commit()
        
        flash('Thank you for reporting. Our team will review it.', 'success')
    
    return redirect(url_for('materials.view', id=id))

# Admin routes
@materials_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('materials.index'))
    
    pending_materials = StudyMaterial.query.filter_by(status='pending').all()
    reported_materials = StudyMaterial.query.join(MaterialReport).filter(
        MaterialReport.status == 'pending'
    ).distinct().all()
    
    return render_template('materials/admin.html', 
                         pending_materials=pending_materials,
                         reported_materials=reported_materials)

@materials_bp.route('/admin/approve/<int:id>', methods=['POST'])
@login_required
def approve_material(id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    material = StudyMaterial.query.get_or_404(id)
    material.status = 'approved'
    material.approved_at = datetime.utcnow()
    material.approved_by = current_user.id
    db.session.commit()
    
    flash('Material listing approved.', 'success')
    return redirect(url_for('materials.admin'))

@materials_bp.route('/admin/reject/<int:id>', methods=['POST'])
@login_required
def reject_material(id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    material = StudyMaterial.query.get_or_404(id)
    material.status = 'rejected'
    db.session.commit()
    
    flash('Material listing rejected.', 'success')
    return redirect(url_for('materials.admin'))

@materials_bp.route('/admin/resolve-report/<int:id>', methods=['POST'])
@login_required
def resolve_report(id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    report = MaterialReport.query.get_or_404(id)
    action = request.form.get('action')
    
    if action == 'dismiss':
        report.status = 'dismissed'
    elif action == 'remove':
        report.status = 'resolved'
        report.material.status = 'removed'
    
    report.resolved_at = datetime.utcnow()
    report.resolved_by = current_user.id
    db.session.commit()
    
    flash('Report resolved.', 'success')
    return redirect(url_for('materials.admin'))

@materials_bp.route('/<int:id>/purchase', methods=['POST'])
@login_required
def purchase(id):
    try:
        material = StudyMaterial.query.get_or_404(id)
        
        if material.seller_id == current_user.id:
            return jsonify({
                'success': False,
                'message': 'You cannot purchase your own material'
            }), 400
        
        if material.status != 'approved':
            return jsonify({
                'success': False,
                'message': 'This material is not available for purchase'
            }), 400
        
        purchase = MaterialPurchase(
            material_id=id,
            buyer_id=current_user.id,
            seller_id=material.seller_id,
            price=material.price
        )
        
        material.status = 'sold'
        db.session.add(purchase)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Purchase request submitted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error processing purchase: {str(e)}'
        }), 400 