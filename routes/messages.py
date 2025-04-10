from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Message, User, StudyMaterial, LostFoundItem
from forms import MessageForm
from app import db
from datetime import datetime

messages = Blueprint('messages', __name__, url_prefix='/messages')

@messages.route('/')
@login_required
def inbox():
    form = MessageForm()
    message_type = request.args.get('message_type', '')
    
    # Get all messages for the current user
    query = Message.query.filter(
        (Message.sender_id == current_user.id) | 
        (Message.receiver_id == current_user.id)
    )
    
    if message_type:
        query = query.filter_by(item_type=message_type)
    
    messages = query.order_by(Message.created_at.desc()).all()
    
    # Group messages by conversation
    conversations = []
    seen_users = set()
    for msg in messages:
        other_user_id = msg.sender_id if msg.receiver_id == current_user.id else msg.receiver_id
        if other_user_id not in seen_users:
            other_user = msg.sender if msg.receiver_id == current_user.id else msg.receiver
            conversations.append({
                'user': other_user,
                'last_message': msg,
                'unread_count': Message.query.filter_by(
                    sender_id=other_user_id,
                    receiver_id=current_user.id,
                    read=False,
                    item_type=message_type if message_type else None
                ).count()
            })
            seen_users.add(other_user_id)
    
    return render_template('messages/chat.html', 
                         conversations=conversations, 
                         other_user=None,
                         messages=[],
                         message_type=message_type)

@messages.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    form = MessageForm()
    
    # Get all messages between current user and other user
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    # Mark messages as read
    for msg in messages:
        if msg.receiver_id == current_user.id and not msg.read:
            msg.read = True
    db.session.commit()
    
    # Get all conversations for the sidebar
    all_messages = Message.query.filter(
        (Message.sender_id == current_user.id) | 
        (Message.receiver_id == current_user.id)
    ).order_by(Message.created_at.desc()).all()
    
    conversations = []
    seen_users = set()
    for msg in all_messages:
        other_user_id = msg.sender_id if msg.receiver_id == current_user.id else msg.receiver_id
        if other_user_id not in seen_users:
            conversations.append({
                'user': msg.sender if msg.receiver_id == current_user.id else msg.receiver,
                'last_message': msg,
                'unread_count': Message.query.filter_by(
                    sender_id=other_user_id,
                    receiver_id=current_user.id,
                    read=False
                ).count()
            })
            seen_users.add(other_user_id)
    
    return render_template('messages/chat.html', 
                         conversations=conversations,
                         other_user=other_user,
                         messages=messages)

@messages.route('/send_message', methods=['POST'])
@login_required
def send_message():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        
        if not receiver_id or not content:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        # Verify receiver exists
        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({'success': False, 'error': 'Receiver not found'}), 404
            
        try:
            # Create and save the message
            message = Message(
                sender_id=current_user.id,
                receiver_id=receiver_id,
                content=content,
                created_at=datetime.utcnow(),
                read=False
            )
            
            db.session.add(message)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': {
                    'id': message.id,
                    'sender_id': message.sender_id,
                    'receiver_id': message.receiver_id,
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                    'read': message.read
                }
            })
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            return jsonify({'success': False, 'error': 'Database error occurred'}), 500
            
    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@messages.route('/api/unread-count')
@login_required
def unread_count():
    """Get number of unread messages for the current user"""
    count = Message.query.filter_by(receiver_id=current_user.id, read=False).count()
    return jsonify({'count': count})

@messages.route('/chat/<int:user_id>/updates')
@login_required
def message_updates(user_id):
    """Get new messages and read status updates since a given timestamp"""
    try:
        since = request.args.get('since')
        if not since:
            return jsonify({'error': 'Missing since parameter'}), 400
            
        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        
        # Get new messages
        new_messages = Message.query.filter(
            Message.created_at > since_dt,
            ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
            ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.created_at.asc()).all()
        
        # Get messages that have been read since last update
        read_messages = Message.query.filter(
            Message.sender_id == current_user.id,
            Message.receiver_id == user_id,
            Message.read == True,
            Message.created_at <= since_dt
        ).with_entities(Message.id).all()
        
        return jsonify({
            'messages': [{
                'id': msg.id,
                'sender_id': msg.sender_id,
                'receiver_id': msg.receiver_id,
                'content': msg.content,
                'created_at': msg.created_at.isoformat(),
                'read': msg.read
            } for msg in new_messages],
            'read_messages': [msg.id for msg in read_messages]
        })
        
    except Exception as e:
        print(f"Error in message updates: {str(e)}")
        return jsonify({'error': str(e)}), 500
