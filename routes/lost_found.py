from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from models import db, LostItem, FoundItem, LostFoundChat, ItemVerification, LostFoundItem, Message
from werkzeug.utils import secure_filename
from forms import LostItemForm, FoundItemForm, LostFoundForm
from extensions import socketio
import os
from datetime import datetime, timedelta
from sqlalchemy import or_

lost_found_bp = Blueprint('lost_found', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def find_potential_matches(item, is_lost=True):
    """Find potential matches for a lost/found item based on category, date, and location."""
    if is_lost:
        # For lost items, find matching found items
        matches = FoundItem.query.filter(
            FoundItem.category == item.category,
            FoundItem.date_found >= item.date_lost - timedelta(days=7),
            FoundItem.date_found <= item.date_lost + timedelta(days=7),
            FoundItem.is_resolved == False
        ).all()
    else:
        # For found items, find matching lost items
        matches = LostItem.query.filter(
            LostItem.category == item.category,
            LostItem.date_lost >= item.date_found - timedelta(days=7),
            LostItem.date_lost <= item.date_found + timedelta(days=7),
            LostItem.status == 'active'
        ).all()
    
    return matches

@lost_found_bp.route('/')
def index():
    """Display all lost and found items with filters"""
    form = LostFoundForm()
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    item_type = request.args.get('type', '')
    status = request.args.get('status', '')
    search_query = request.args.get('search_query', '')
    sort = request.args.get('sort', 'newest')
    
    # Build query
    query = LostFoundItem.query
    
    # Apply filters
    if search_query:
        query = query.filter(
            (LostFoundItem.title.ilike(f'%{search_query}%')) |
            (LostFoundItem.description.ilike(f'%{search_query}%'))
        )
    if category:
        query = query.filter_by(category=category)
    if item_type:
        query = query.filter_by(type=item_type)
    if status:
        query = query.filter_by(status=status)
    
    # Apply sorting
    if sort == 'oldest':
        query = query.order_by(LostFoundItem.created_at.asc())
    else:  # newest first (default)
        query = query.order_by(LostFoundItem.created_at.desc())
    
    # Paginate results
    items = query.paginate(page=page, per_page=12, error_out=False)
    
    # Get distinct categories
    categories = db.session.query(LostFoundItem.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]  # Extract category names and filter out None
    
    # Get unread message count for Lost & Found
    unread_count = 0
    if current_user.is_authenticated:
        unread_count = Message.query.filter_by(
            receiver_id=current_user.id,
            message_type='lost_found',
            read=False
        ).count()
    
    return render_template('lost_found/index.html',
                         items=items,
                         form=form,
                         categories=categories,
                         current_category=category,
                         current_type=item_type,
                         current_sort=sort,
                         status=status,
                         search_query=search_query,
                         unread_count=unread_count)

@lost_found_bp.route('/report', methods=['GET', 'POST'])
@login_required
def report_item():
    form = LostFoundForm()
    if form.validate_on_submit():
        # Handle file upload
        image_url = None
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_url = url_for('static', filename=f'uploads/lost_found/{filename}')

        # Create new item
        item = LostFoundItem(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            location=form.location.data,
            date=form.date_found.data,
            type=form.item_type.data,
            image_path=image_url,
            reporter_id=current_user.id
        )
        
        db.session.add(item)
        db.session.commit()
        
        flash('Item reported successfully!', 'success')
        return redirect(url_for('lost_found.index'))
    
    return render_template('lost_found/report.html', form=form)

@lost_found_bp.route('/item/<int:id>')
def show_item(id):
    """Display details of a specific item"""
    item = LostFoundItem.query.get_or_404(id)
    return render_template('lost_found/show.html', item=item)

@lost_found_bp.route('/item/<int:id>/claim', methods=['POST'])
@login_required
def claim_item(id):
    """Claim a found item or mark a lost item as found"""
    item = LostFoundItem.query.get_or_404(id)
    
    if item.reporter_id == current_user.id:
        flash('You cannot claim your own item!', 'error')
        return redirect(url_for('lost_found.show_item', id=id))
    
    if item.status != 'open':
        flash('This item has already been claimed!', 'error')
        return redirect(url_for('lost_found.show_item', id=id))
    
    item.status = 'claimed'
    item.claimer_id = current_user.id
    db.session.commit()
    
    # Create a message thread between reporter and claimer
    message = Message(
        sender_id=current_user.id,
        receiver_id=item.reporter_id,
        content=f"I would like to claim the {item.type} item: {item.title}",
        item_id=item.id
    )
    db.session.add(message)
    db.session.commit()
    
    flash('Item claimed successfully! Check your messages to contact the reporter.', 'success')
    return redirect(url_for('lost_found.show_item', id=id))

@lost_found_bp.route('/item/<int:id>/verify', methods=['POST'])
@login_required
def verify_item(id):
    """Verify a claimed item"""
    item = LostFoundItem.query.get_or_404(id)
    
    if item.reporter_id != current_user.id and item.claimer_id != current_user.id:
        flash('You are not authorized to verify this item!', 'error')
        return redirect(url_for('lost_found.show_item', id=id))
    
    verification_details = request.form.get('verification_details')
    if not verification_details:
        flash('Please provide verification details', 'error')
        return redirect(url_for('lost_found.show_item', id=id))
    
    item.verification_status = 'verified'
    item.verification_details = verification_details
    item.status = 'closed'
    db.session.commit()
    
    flash('Item verified successfully!', 'success')
    return redirect(url_for('lost_found.show_item', id=id))

@lost_found_bp.route('/admin/items')
@login_required
def admin_items():
    """Admin view of all items"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('lost_found.index'))
    
    items = LostFoundItem.query.order_by(LostFoundItem.created_at.desc()).all()
    return render_template('lost_found/admin.html', items=items)

@lost_found_bp.route('/admin/item/<int:id>/delete', methods=['POST'])
@login_required
def admin_delete_item(id):
    """Admin delete an item"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    item = LostFoundItem.query.get_or_404(id)
    try:
        if item.image_url:
            os.remove(item.image_url)
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Item deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@lost_found_bp.route('/show/lost/<int:id>')
def show_lost(id):
    """Show details of a lost item."""
    item = LostItem.query.get_or_404(id)
    return render_template('lost_found/show_lost.html', item=item)

@lost_found_bp.route('/show/found/<int:id>')
def show_found(id):
    """Show details of a found item."""
    item = FoundItem.query.get_or_404(id)
    return render_template('lost_found/show_found.html', item=item)

@lost_found_bp.route('/delete/lost/<int:id>', methods=['POST'])
@login_required
def delete_lost(id):
    """Delete a lost item."""
    item = LostItem.query.get_or_404(id)
    if item.user_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to delete this item.', 'error')
        return redirect(url_for('lost_found.index'))
    
    db.session.delete(item)
    db.session.commit()
    flash('Lost item deleted successfully.', 'success')
    return redirect(url_for('lost_found.index'))

@lost_found_bp.route('/delete/found/<int:id>', methods=['POST'])
@login_required
def delete_found(id):
    """Delete a found item."""
    item = FoundItem.query.get_or_404(id)
    if item.user_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to delete this item.', 'error')
        return redirect(url_for('lost_found.index'))
    
    db.session.delete(item)
    db.session.commit()
    flash('Found item deleted successfully.', 'success')
    return redirect(url_for('lost_found.index'))

@lost_found_bp.route('/chat/<int:lost_id>/<int:found_id>')
@login_required
def chat(lost_id, found_id):
    """Render the chat interface for a specific lost/found item match"""
    lost_item = LostItem.query.get_or_404(lost_id)
    found_item = FoundItem.query.get_or_404(found_id)
    
    # Verify that the current user is either the owner or finder
    if current_user.id not in [lost_item.user_id, found_item.user_id]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get chat history
    messages = LostFoundChat.query.filter(
        ((LostFoundChat.lost_item_id == lost_id) & (LostFoundChat.found_item_id == found_id)) |
        ((LostFoundChat.lost_item_id == found_id) & (LostFoundChat.found_item_id == lost_id))
    ).order_by(LostFoundChat.created_at).all()
    
    return render_template('lost_found/chat.html',
                         lost_item=lost_item,
                         found_item=found_item,
                         messages=messages)

@socketio.on('join')
def on_join(data):
    """Handle user joining a chat room"""
    room = f"chat_{data['lost_id']}_{data['found_id']}"
    join_room(room)
    emit('status', {'msg': f"{current_user.username} has joined the room."}, room=room)

@socketio.on('leave')
def on_leave(data):
    """Handle user leaving a chat room"""
    room = f"chat_{data['lost_id']}_{data['found_id']}"
    leave_room(room)
    emit('status', {'msg': f"{current_user.username} has left the room."}, room=room)

@socketio.on('message')
def handle_message(data):
    """Handle incoming chat messages"""
    lost_id = data['lost_id']
    found_id = data['found_id']
    message = data['message']
    
    # Verify that the current user is either the owner or finder
    lost_item = LostItem.query.get(lost_id)
    found_item = FoundItem.query.get(found_id)
    
    if not lost_item or not found_item or current_user.id not in [lost_item.user_id, found_item.user_id]:
        emit('error', {'msg': 'Unauthorized'})
        return
    
    # Create chat message
    chat_message = LostFoundChat(
        lost_item_id=lost_id,
        found_item_id=found_id,
        sender_id=current_user.id,
        receiver_id=found_item.user_id if current_user.id == lost_item.user_id else lost_item.user_id,
        message=message
    )
    db.session.add(chat_message)
    db.session.commit()
    
    # Emit message to room
    room = f"chat_{lost_id}_{found_id}"
    emit('message', {
        'user': current_user.username,
        'message': message,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }, room=room)

@lost_found_bp.route('/api/messages/<int:lost_id>/<int:found_id>')
@login_required
def get_messages(lost_id, found_id):
    """Get chat history for a specific lost/found item match"""
    messages = LostFoundChat.query.filter(
        ((LostFoundChat.lost_item_id == lost_id) & (LostFoundChat.found_item_id == found_id)) |
        ((LostFoundChat.lost_item_id == found_id) & (LostFoundChat.found_item_id == lost_id))
    ).order_by(LostFoundChat.created_at).all()
    
    return jsonify([{
        'id': msg.id,
        'sender': msg.sender.username,
        'message': msg.message,
        'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'is_read': msg.is_read
    } for msg in messages])

@lost_found_bp.route('/api/messages/<int:lost_id>/<int:found_id>/mark_read', methods=['POST'])
@login_required
def mark_messages_read(lost_id, found_id):
    """Mark messages as read for a specific chat"""
    messages = LostFoundChat.query.filter(
        ((LostFoundChat.lost_item_id == lost_id) & (LostFoundChat.found_item_id == found_id)) |
        ((LostFoundChat.lost_item_id == found_id) & (LostFoundChat.found_item_id == lost_id)),
        LostFoundChat.receiver_id == current_user.id,
        LostFoundChat.is_read == False
    ).all()
    
    for message in messages:
        message.is_read = True
    
    db.session.commit()
    return jsonify({'success': True})

@lost_found_bp.route('/api/verify_match/<int:lost_id>/<int:found_id>', methods=['POST'])
@login_required
def verify_match(lost_id, found_id):
    """Handle match verification between lost and found items"""
    lost_item = LostItem.query.get_or_404(lost_id)
    found_item = FoundItem.query.get_or_404(found_id)
    
    # Verify that the current user is either the owner or finder
    if current_user.id not in [lost_item.user_id, found_item.user_id]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get or create verification details
    verification = ItemVerification.query.filter_by(
        lost_item_id=lost_id,
        found_item_id=found_id
    ).first()
    
    if not verification:
        verification = ItemVerification(
            lost_item_id=lost_id,
            found_item_id=found_id
        )
        db.session.add(verification)
    
    # Update verification status based on user role
    if current_user.id == lost_item.user_id:
        verification.owner_confirmation = True
    else:
        verification.finder_confirmation = True
    
    # If both parties have confirmed, mark items as resolved
    if verification.owner_confirmation and verification.finder_confirmation:
        lost_item.status = 'found'
        lost_item.found_at = datetime.utcnow()
        lost_item.found_by = found_item.user_id
        found_item.is_resolved = True
        
        # Add system message to chat
        chat_message = LostFoundChat(
            lost_item_id=lost_id,
            found_item_id=found_id,
            sender_id=current_user.id,
            receiver_id=found_item.user_id if current_user.id == lost_item.user_id else lost_item.user_id,
            message="Match verified! You can now exchange contact information.",
            is_system=True
        )
        db.session.add(chat_message)
    
    db.session.commit()
    return jsonify({'success': True})

@lost_found_bp.route('/verification/<int:item_id>')
@login_required
def verification_chat(item_id):
    # Determine if it's a lost or found item
    item = LostItem.query.get(item_id)
    item_type = 'lost'
    if not item:
        item = FoundItem.query.get(item_id)
        item_type = 'found'
        if not item:
            flash('Item not found', 'error')
            return redirect(url_for('lost_found.index'))

    # Get verification status
    verification = ItemVerification.query.filter_by(
        lost_item_id=item_id if item_type == 'lost' else None,
        found_item_id=item_id if item_type == 'found' else None
    ).first()

    # Get chat messages
    messages = LostFoundChat.query.filter_by(
        lost_item_id=item_id if item_type == 'lost' else None,
        found_item_id=item_id if item_type == 'found' else None
    ).order_by(LostFoundChat.created_at).all()

    # Calculate progress
    if verification:
        if verification.owner_confirmation and verification.finder_confirmation:
            current_step = 6
            progress = 100
            verification_completed = True
        else:
            current_step = 5
            progress = 80
            verification_completed = False
    else:
        current_step = 1
        progress = 20
        verification_completed = False

    return render_template('lost_found/verification_chat.html',
                         item=item,
                         item_type=item_type,
                         messages=messages,
                         current_step=current_step,
                         progress=progress,
                         verification_completed=verification_completed)

@lost_found_bp.route('/verification/<int:item_id>/step1', methods=['POST'])
@login_required
def verification_step1(item_id):
    data = request.get_json()
    is_match = data.get('is_match', False)

    # Create or update verification record
    verification = ItemVerification.query.filter_by(lost_item_id=item_id).first()
    if not verification:
        verification = ItemVerification(lost_item_id=item_id)
        db.session.add(verification)

    # Update verification status
    if current_user.id == verification.lost_item.user_id:
        verification.owner_confirmation = is_match
    else:
        verification.finder_confirmation = is_match

    # Add system message
    chat_message = LostFoundChat(
        lost_item_id=item_id,
        sender_id=current_user.id,
        receiver_id=verification.lost_item.user_id if current_user.id != verification.lost_item.user_id else verification.found_item.user_id,
        message="Item verification step 1 completed",
        is_system=True
    )
    db.session.add(chat_message)

    db.session.commit()
    return jsonify({'success': True})

@lost_found_bp.route('/verification/<int:item_id>/step2', methods=['POST'])
@login_required
def verification_step2(item_id):
    data = request.get_json()
    description = data.get('description', '')

    # Add user's description to chat
    verification = ItemVerification.query.filter_by(lost_item_id=item_id).first()
    if not verification:
        return jsonify({'success': False, 'error': 'Verification not found'})

    chat_message = LostFoundChat(
        lost_item_id=item_id,
        sender_id=current_user.id,
        receiver_id=verification.lost_item.user_id if current_user.id != verification.lost_item.user_id else verification.found_item.user_id,
        message=f"Item description: {description}",
        is_system=False
    )
    db.session.add(chat_message)

    # Add system message
    system_message = LostFoundChat(
        lost_item_id=item_id,
        sender_id=current_user.id,
        receiver_id=verification.lost_item.user_id if current_user.id != verification.lost_item.user_id else verification.found_item.user_id,
        message="Item description submitted",
        is_system=True
    )
    db.session.add(system_message)

    db.session.commit()
    return jsonify({'success': True})

@lost_found_bp.route('/verification/<int:item_id>/step3', methods=['POST'])
@login_required
def verification_step3(item_id):
    data = request.get_json()
    location = data.get('location', '')

    # Add user's location details to chat
    verification = ItemVerification.query.filter_by(lost_item_id=item_id).first()
    if not verification:
        return jsonify({'success': False, 'error': 'Verification not found'})

    chat_message = LostFoundChat(
        lost_item_id=item_id,
        sender_id=current_user.id,
        receiver_id=verification.lost_item.user_id if current_user.id != verification.lost_item.user_id else verification.found_item.user_id,
        message=f"Location details: {location}",
        is_system=False
    )
    db.session.add(chat_message)

    # Add system message
    system_message = LostFoundChat(
        lost_item_id=item_id,
        sender_id=current_user.id,
        receiver_id=verification.lost_item.user_id if current_user.id != verification.lost_item.user_id else verification.found_item.user_id,
        message="Location details submitted",
        is_system=True
    )
    db.session.add(system_message)

    db.session.commit()
    return jsonify({'success': True})

@lost_found_bp.route('/verification/<int:item_id>/step4', methods=['POST'])
@login_required
def verification_step4(item_id):
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'No photo uploaded'})

    file = request.files['photo']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'verification_photos', filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)

        # Add photo message to chat
        verification = ItemVerification.query.filter_by(lost_item_id=item_id).first()
        if not verification:
            return jsonify({'success': False, 'error': 'Verification not found'})

        chat_message = LostFoundChat(
            lost_item_id=item_id,
            sender_id=current_user.id,
            receiver_id=verification.lost_item.user_id if current_user.id != verification.lost_item.user_id else verification.found_item.user_id,
            message=f"Verification photo uploaded: {filename}",
            is_system=False
        )
        db.session.add(chat_message)

        # Add system message
        system_message = LostFoundChat(
            lost_item_id=item_id,
            sender_id=current_user.id,
            receiver_id=verification.lost_item.user_id if current_user.id != verification.lost_item.user_id else verification.found_item.user_id,
            message="Verification photo submitted",
            is_system=True
        )
        db.session.add(system_message)

        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Invalid file type'})

@lost_found_bp.route('/verification/<int:item_id>/step5', methods=['POST'])
@login_required
def verification_step5(item_id):
    data = request.get_json()
    is_match = data.get('is_match', False)

    # Update verification record
    verification = ItemVerification.query.filter_by(lost_item_id=item_id).first()
    if not verification:
        return jsonify({'success': False, 'error': 'Verification not found'})

    # Update verification status
    if current_user.id == verification.lost_item.user_id:
        verification.owner_confirmation = is_match
    else:
        verification.finder_confirmation = is_match

    # If both parties confirm, mark item as verified
    if verification.owner_confirmation and verification.finder_confirmation:
        verification.verified_at = datetime.utcnow()
        verification.lost_item.status = 'verified'
        verification.lost_item.found_at = datetime.utcnow()
        verification.lost_item.found_by = current_user.id

    # Add system message
    chat_message = LostFoundChat(
        lost_item_id=item_id,
        sender_id=current_user.id,
        receiver_id=verification.lost_item.user_id if current_user.id != verification.lost_item.user_id else verification.found_item.user_id,
        message="Final verification completed",
        is_system=True
    )
    db.session.add(chat_message)

    db.session.commit()
    return jsonify({'success': True})

@lost_found_bp.route('/chat/<int:item_id>/send', methods=['POST'])
@login_required
def send_chat_message(item_id):
    data = request.get_json()
    message = data.get('message', '')

    if not message:
        return jsonify({'success': False, 'error': 'No message provided'})

    # Get verification record
    verification = ItemVerification.query.filter_by(lost_item_id=item_id).first()
    if not verification:
        return jsonify({'success': False, 'error': 'Verification not found'})

    # Create chat message
    chat_message = LostFoundChat(
        lost_item_id=item_id,
        sender_id=current_user.id,
        receiver_id=verification.lost_item.user_id if current_user.id != verification.lost_item.user_id else verification.found_item.user_id,
        message=message,
        is_system=False
    )
    db.session.add(chat_message)
    db.session.commit()

    return jsonify({'success': True})

@lost_found_bp.route('/item/<int:item_id>')
def detail(item_id):
    """View details of a specific lost or found item"""
    item = LostFoundItem.query.get_or_404(item_id)
    return render_template('lost_found/show.html', item=item)

@lost_found_bp.route('/item/<int:id>/delete', methods=['POST'])
@login_required
def delete_item(id):
    """Delete an item (for item owner)"""
    item = LostFoundItem.query.get_or_404(id)
    
    if item.reporter_id != current_user.id:
        flash('You are not authorized to delete this item.', 'error')
        return redirect(url_for('lost_found.index'))
    
    try:
        if item.image_path:
            # Remove the image file
            image_path = os.path.join(current_app.static_folder, item.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting item.', 'error')
    
    return redirect(url_for('lost_found.index'))