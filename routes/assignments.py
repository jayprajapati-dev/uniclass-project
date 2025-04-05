from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import FileField, TextAreaField
from wtforms.validators import DataRequired
from models import db, Assignment, AssignmentSubmission
from datetime import datetime
import os
from werkzeug.utils import secure_filename

assignments_bp = Blueprint('assignments', __name__)

class SubmissionForm(FlaskForm):
    file = FileField('Assignment File', validators=[DataRequired()])
    notes = TextAreaField('Notes')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@assignments_bp.route('/')
@login_required
def index():
    """View all assignments"""
    assignments = Assignment.query.order_by(Assignment.due_date.desc()).all()
    return render_template('assignments/index.html', assignments=assignments)

@assignments_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new assignment"""
    if request.method == 'POST':
        try:
            title = request.form['title']
            description = request.form['description']
            due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
            
            assignment = Assignment(
                title=title,
                description=description,
                due_date=due_date,
                created_by=current_user.id
            )
            
            db.session.add(assignment)
            db.session.commit()
            
            flash('Assignment created successfully!', 'success')
            return redirect(url_for('assignments.index'))
        except Exception as e:
            flash(f'Error creating assignment: {str(e)}', 'danger')
    
    return render_template('assignments/create.html')

@assignments_bp.route('/<int:id>')
@login_required
def view(id):
    """View a specific assignment"""
    assignment = Assignment.query.get_or_404(id)
    submissions = AssignmentSubmission.query.filter_by(assignment_id=id).all()
    return render_template('assignments/view.html', 
                         assignment=assignment,
                         submissions=submissions)

@assignments_bp.route('/<int:id>/submit', methods=['POST'])
@login_required
def submit(id):
    """Submit an assignment"""
    try:
        assignment = Assignment.query.get_or_404(id)
        
        # Check if already submitted
        existing = AssignmentSubmission.query.filter_by(
            assignment_id=id,
            student_id=current_user.id
        ).first()
        
        if existing:
            flash('You have already submitted this assignment.', 'warning')
            return redirect(url_for('assignments.view', id=id))
        
        submission = AssignmentSubmission(
            assignment_id=id,
            student_id=current_user.id,
            submission_date=datetime.now()
        )
        
        db.session.add(submission)
        db.session.commit()
        
        flash('Assignment submitted successfully!', 'success')
        return redirect(url_for('assignments.view', id=id))
    except Exception as e:
        flash(f'Error submitting assignment: {str(e)}', 'danger')
        return redirect(url_for('assignments.view', id=id))

@assignments_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an assignment"""
    assignment = Assignment.query.get_or_404(id)
    
    if assignment.created_by != current_user.id and not current_user.is_admin:
        flash('You can only edit your own assignments.', 'danger')
        return redirect(url_for('assignments.index'))
    
    if request.method == 'POST':
        try:
            assignment.title = request.form['title']
            assignment.description = request.form['description']
            assignment.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
            
            db.session.commit()
            flash('Assignment updated successfully!', 'success')
            return redirect(url_for('assignments.view', id=id))
        except Exception as e:
            flash(f'Error updating assignment: {str(e)}', 'danger')
    
    return render_template('assignments/edit.html', assignment=assignment)

@assignments_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete an assignment"""
    assignment = Assignment.query.get_or_404(id)
    
    if assignment.created_by != current_user.id and not current_user.is_admin:
        flash('You can only delete your own assignments.', 'danger')
        return redirect(url_for('assignments.index'))
    
    try:
        # Delete all submissions first
        AssignmentSubmission.query.filter_by(assignment_id=id).delete()
        db.session.delete(assignment)
        db.session.commit()
        flash('Assignment deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting assignment: {str(e)}', 'danger')
    
    return redirect(url_for('assignments.index')) 