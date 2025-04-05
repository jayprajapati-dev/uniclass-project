from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Notification, User
from datetime import datetime
from flask_mail import Mail, Message

notifications_bp = Blueprint('notifications', __name__)
mail = Mail()

def create_notification(user_id, title, message, type, link=None):
    """Helper function to create a notification"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        link=link
    )
    db.session.add(notification)
    db.session.commit()
    return notification

@notifications_bp.route('/')
@login_required
def get_notifications():
    """Get all notifications for current user"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat(),
        'link': n.link
    } for n in notifications])

@notifications_bp.route('/unread')
@login_required
def get_unread_count():
    """Get count of unread notifications"""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({'count': count})

@notifications_bp.route('/<int:id>/read', methods=['POST'])
@login_required
def mark_as_read(id):
    """Mark a notification as read"""
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_as_read():
    """Mark all notifications as read"""
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

@notifications_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_notification():
    if not current_user.is_admin:
        flash('Only administrators can create notifications', 'error')
        return redirect(url_for('notifications.list_notifications'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        notification_type = request.form.get('type')
        target_audience = request.form.get('target_audience')
        
        if not all([title, message, notification_type, target_audience]):
            flash('All fields are required', 'error')
            return redirect(url_for('notifications.create_notification'))
        
        # Create notification in database
        notification = Notification(
            title=title,
            message=message,
            type=notification_type,
            target_audience=target_audience,
            created_by=current_user.id
        )
        db.session.add(notification)
        db.session.commit()
        
        # Send email notification
        send_email_notification(notification)
        
        flash('Notification created and sent successfully', 'success')
        return redirect(url_for('notifications.list_notifications'))
    
    return render_template('notifications/create.html')

@notifications_bp.route('/<int:id>')
@login_required
def view_notification(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view this notification', 'error')
        return redirect(url_for('notifications.list_notifications'))
    
    # Mark as read if not already
    if not notification.read:
        notification.read = True
        notification.read_at = datetime.utcnow()
        db.session.commit()
    
    return render_template('notifications/view.html', notification=notification)

@notifications_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_notification(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this notification', 'error')
        return redirect(url_for('notifications.list_notifications'))
    
    db.session.delete(notification)
    db.session.commit()
    
    flash('Notification deleted successfully', 'success')
    return redirect(url_for('notifications.list_notifications'))

def send_email_notification(notification):
    try:
        # Get target users based on audience
        if notification.target_audience == 'all':
            users = User.query.all()
        elif notification.target_audience == 'students':
            users = User.query.filter_by(is_admin=False).all()
        elif notification.target_audience == 'admins':
            users = User.query.filter_by(is_admin=True).all()
        else:
            return
        
        # Send email to each user
        for user in users:
            msg = Message(
                subject=notification.title,
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            msg.body = f"""
            {notification.message}
            
            Type: {notification.type}
            Sent by: {current_user.username}
            """
            
            if notification.type == 'study_material':
                msg.body += "\nPlease check the study materials section for more details."
            elif notification.type == 'timetable':
                msg.body += "\nPlease check the timetable section for more details."
            
            mail.send(msg)
            
    except Exception as e:
        current_app.logger.error(f'Failed to send email notification: {str(e)}')
        flash('Failed to send email notification', 'error') 