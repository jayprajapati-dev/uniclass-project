from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Message, User, LostItem, FoundItem

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/messages')
@login_required
def inbox():
    """Show user's message inbox"""
    received_messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).all()
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    return render_template('messages/inbox.html', received_messages=received_messages, sent_messages=sent_messages)

@messages_bp.route('/messages/send/<item_type>/<int:item_id>/<int:receiver_id>', methods=['GET', 'POST'])
@login_required
def send_message(item_type, item_id, receiver_id):
    """Send a message to another user"""
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('Message cannot be empty', 'error')
            return redirect(request.referrer)

        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content,
            item_id=item_id if item_id else None,
            item_type=item_type if item_type else None
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully', 'success')
        return redirect(url_for('messages_bp.inbox'))

    receiver = User.query.get_or_404(receiver_id)
    return render_template('messages/send.html', receiver=receiver, item_type=item_type, item_id=item_id)

@messages_bp.route('/messages/conversation/<int:user_id>')
@login_required
def conversation(user_id):
    """Show conversation with a specific user"""
    other_user = User.query.get_or_404(user_id)
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    # Mark messages as read
    for message in messages:
        if message.receiver_id == current_user.id and not message.read:
            message.read = True
    db.session.commit()
    
    return render_template('messages/conversation.html', messages=messages, other_user=other_user)

@messages_bp.route('/messages/api/unread-count')
@login_required
def unread_count():
    """Get number of unread messages for the current user"""
    count = Message.query.filter_by(receiver_id=current_user.id, read=False).count()
    return jsonify({'count': count})
