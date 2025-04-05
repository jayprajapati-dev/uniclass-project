from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, LostItem, FoundItem, User, Feedback

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/feedback/give/<item_type>/<int:item_id>/<int:reviewee_id>', methods=['GET', 'POST'])
@login_required
def give_feedback(item_type, item_id, reviewee_id):
    """Give feedback to another user after a transaction"""
    # Check if feedback already exists
    existing_feedback = Feedback.query.filter_by(
        item_id=item_id,
        item_type=item_type,
        reviewer_id=current_user.id
    ).first()
    
    if existing_feedback:
        flash('You have already given feedback for this transaction', 'warning')
        return redirect(url_for('lost_found.index'))
    
    # Get the item and reviewee
    reviewee = User.query.get_or_404(reviewee_id)
    item = None
    if item_type == 'lost':
        item = LostItem.query.get_or_404(item_id)
    else:
        item = FoundItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        feedback = Feedback(
            item_id=item_id,
            item_type=item_type,
            reviewer_id=current_user.id,
            reviewee_id=reviewee_id,
            rating=int(request.form.get('overall_rating')),
            review=request.form.get('review'),
            communication_rating=int(request.form.get('communication_rating')),
            timeliness_rating=int(request.form.get('timeliness_rating')),
            overall_rating=int(request.form.get('overall_rating'))
        )
        db.session.add(feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('lost_found.index'))
    
    return render_template('feedback/give.html', 
                         reviewee=reviewee, 
                         item=item, 
                         item_type=item_type)

@feedback_bp.route('/feedback/user/<int:user_id>')
def user_feedback(user_id):
    """View all feedback for a user"""
    user = User.query.get_or_404(user_id)
    received_feedback = Feedback.query.filter_by(reviewee_id=user_id).order_by(Feedback.created_at.desc()).all()
    
    # Calculate average ratings
    if received_feedback:
        avg_communication = sum(f.communication_rating for f in received_feedback) / len(received_feedback)
        avg_timeliness = sum(f.timeliness_rating for f in received_feedback) / len(received_feedback)
        avg_overall = sum(f.overall_rating for f in received_feedback) / len(received_feedback)
    else:
        avg_communication = avg_timeliness = avg_overall = 0
    
    return render_template('feedback/user.html',
                         user=user,
                         feedback=received_feedback,
                         avg_communication=avg_communication,
                         avg_timeliness=avg_timeliness,
                         avg_overall=avg_overall)
