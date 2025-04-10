from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, StudyMaterial, MaterialPurchase, MaterialReport, Message, User
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
@login_required
def index():
    """Display all study materials with filters"""
    form = MaterialSearchForm()
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search_query', '')
    material_type = request.args.get('material_type', '')
    branch = request.args.get('branch', '')
    semester = request.args.get('semester', '')
    condition = request.args.get('condition', '')
    sort_by = request.args.get('sort_by', '')
    
    # Build query
    query = StudyMaterial.query
    
    # Apply filters
    if search_query:
        query = query.filter(
            (StudyMaterial.title.ilike(f'%{search_query}%')) |
            (StudyMaterial.description.ilike(f'%{search_query}%'))
        )
    if material_type:
        query = query.filter_by(material_type=material_type)
    if branch:
        query = query.filter_by(branch=branch)
    if semester:
        query = query.filter_by(semester=semester)
    if condition:
        query = query.filter_by(condition=condition)
    
    # Apply sorting
    if sort_by == 'price_asc':
        query = query.order_by(StudyMaterial.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(StudyMaterial.price.desc())
    elif sort_by == 'date_asc':
        query = query.order_by(StudyMaterial.created_at.asc())
    else:  # Default to newest first
        query = query.order_by(StudyMaterial.created_at.desc())
    
    # Paginate results
    materials = query.paginate(page=page, per_page=12, error_out=False)
    
    # Get unread message count for Study Materials
    unread_count = Message.query.filter_by(
        receiver_id=current_user.id,
        message_type='material',
        read=False
    ).count()
    
    return render_template('materials/index.html',
                         materials=materials,
                         form=form,
                         search_query=search_query,
                         material_type=material_type,
                         branch=branch,
                         semester=semester,
                         condition=condition,
                         sort_by=sort_by,
                         unread_count=unread_count)

@materials_bp.route('/sell', methods=['GET', 'POST'])
@login_required
def sell_material():
    form = StudyMaterialForm()
    if form.validate_on_submit():
        try:
            # Handle file upload
            image_filename = None
            if form.image.data:
                image = form.image.data
                filename = secure_filename(image.filename)
                image_filename = f"uploads/materials/{current_user.id}_{filename}"
                image_path = os.path.join(current_app.static_folder, image_filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image.save(image_path)

            # Create new study material
            material = StudyMaterial(
                title=form.title.data,
                subject=form.subject.data,
                material_type=form.material_type.data,
                branch=form.branch.data,
                semester=form.semester.data,
                description=form.description.data,
                price=form.price.data,
                condition=form.condition.data,
                seller_id=current_user.id,
                image_path=image_filename,
                status='available'
            )
            
            db.session.add(material)
            db.session.commit()
            
            flash('Your study material has been listed for sale!', 'success')
            return redirect(url_for('materials.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('materials/create.html', form=form)

@materials_bp.route('/my-materials')
@login_required
def my_materials():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    materials = StudyMaterial.query.filter_by(seller_id=current_user.id)\
        .order_by(StudyMaterial.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('materials/list.html', materials=materials)

@materials_bp.route('/view/<int:id>')
def view_material(id):
    material = StudyMaterial.query.get_or_404(id)
    report_form = MaterialReportForm()
    return render_template('materials/view.html', material=material, report_form=report_form)

@materials_bp.route('/buy/<int:id>', methods=['POST'])
@login_required
def buy_material(id):
    material = StudyMaterial.query.get_or_404(id)
    
    if material.seller_id == current_user.id:
        flash('You cannot buy your own material!', 'danger')
        return redirect(url_for('materials.view_material', id=id))
    
    if material.status != 'available':
        flash('This material is no longer available!', 'danger')
        return redirect(url_for('materials.view_material', id=id))
    
    try:
        # Create purchase record
        purchase = MaterialPurchase(
            material_id=material.id,
            buyer_id=current_user.id,
            seller_id=material.seller_id,
            price=material.price
        )
        
        # Update material status
        material.status = 'sold'
        
        db.session.add(purchase)
        db.session.commit()
        
        flash('Purchase successful!', 'success')
        return redirect(url_for('materials.view_material', id=id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('materials.view_material', id=id))

@materials_bp.route('/<int:id>/contact', methods=['POST'])
@login_required
def contact_seller(id):
    material = StudyMaterial.query.get_or_404(id)
    if material.seller_id == current_user.id:
        flash('You cannot contact yourself.', 'danger')
        return redirect(url_for('materials.view_material', id=id))

    message = Message(
        sender_id=current_user.id,
        receiver_id=material.seller_id,
        content=request.form.get('message'),
        message_type='text'
    )
    db.session.add(message)
    db.session.commit()

    flash('Message sent to seller.', 'success')
    return redirect(url_for('materials.view_material', id=id))

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
    
    return redirect(url_for('materials.view_material', id=id))

@materials_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_material(id):
    material = StudyMaterial.query.get_or_404(id)
    
    # Check if the current user is the seller
    if current_user.id != material.seller_id:
        flash('You are not authorized to delete this material.', 'danger')
        return redirect(url_for('materials.view_material', id=id))
    
    try:
        # Delete the material image if it exists
        if material.image_path:
            image_path = os.path.join(current_app.static_folder, material.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Delete the material
        db.session.delete(material)
        db.session.commit()
        
        flash('Material deleted successfully.', 'success')
        return redirect(url_for('materials.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the material: {str(e)}', 'danger')
        return redirect(url_for('materials.view_material', id=id))

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