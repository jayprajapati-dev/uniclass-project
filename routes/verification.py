from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, LostItem, FoundItem, ItemVerification, LostFoundChat
from datetime import datetime
import os

verification_bp = Blueprint('verification', __name__)

@verification_bp.route('/verify/<string:item_type>/<int:item_id>', methods=['GET', 'POST'])
@login_required
def verify_item(item_type, item_id):
    """Start or continue the verification process for an item."""
    if item_type == 'lost':
        item = LostItem.query.get_or_404(item_id)
        potential_matches = item.potential_matches
    else:
        item = FoundItem.query.get_or_404(item_id)
        potential_matches = item.matching_lost_items

    # Check if verification already exists
    verification = None
    if item_type == 'lost':
        verification = ItemVerification.query.filter_by(lost_item_id=item_id).first()
    else:
        verification = ItemVerification.query.filter_by(found_item_id=item_id).first()

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'start_verification':
            # Create new verification
            match_id = request.form.get('match_id')
            if item_type == 'lost':
                verification = ItemVerification(lost_item_id=item_id, found_item_id=match_id)
            else:
                verification = ItemVerification(lost_item_id=match_id, found_item_id=item_id)
            
            # Add initial system message
            system_msg = LostFoundChat(
                verification=verification,
                message="Hi! I see you've reported a lost/found item. Let's verify if this is the correct one.",
                is_system=True
            )
            db.session.add(verification)
            db.session.add(system_msg)
            db.session.commit()
            
            return redirect(url_for('verification.chat', verification_id=verification.id))
        
        elif action == 'confirm_step':
            step = request.form.get('step')
            if step == '1':
                # Initial confirmation
                if request.form.get('confirmed') == 'yes':
                    verification.verification_step = 2
                    system_msg = LostFoundChat(
                        verification=verification,
                        message="Please provide a detailed description of the item (color, size, unique feature).",
                        is_system=True
                    )
                    db.session.add(system_msg)
                else:
                    verification.verification_status = 'rejected'
            
            elif step == '2':
                # Save description
                verification.owner_description = request.form.get('description')
                verification.verification_step = 3
                system_msg = LostFoundChat(
                    verification=verification,
                    message="Can you confirm where and when you lost/found this item?",
                    is_system=True
                )
                db.session.add(system_msg)
            
            elif step == '3':
                # Save location and date
                verification.owner_location_date = request.form.get('location_date')
                verification.verification_step = 4
                system_msg = LostFoundChat(
                    verification=verification,
                    message="Please upload a photo of the item for verification purposes.",
                    is_system=True
                )
                db.session.add(system_msg)
            
            elif step == '4':
                # Handle photo upload
                if 'photo' in request.files:
                    photo = request.files['photo']
                    if photo:
                        filename = f"verification_{verification.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                        photo.save(os.path.join('static/uploads/verification', filename))
                        verification.owner_photo = filename
                
                verification.verification_step = 5
                system_msg = LostFoundChat(
                    verification=verification,
                    message="Based on the description and photo, is this indeed your lost item?",
                    is_system=True
                )
                db.session.add(system_msg)
            
            elif step == '5':
                # Final confirmation
                if request.form.get('final_confirmation') == 'yes':
                    if item_type == 'lost':
                        verification.owner_confirmation = True
                        if verification.finder_confirmation:
                            verification.verification_status = 'verified'
                    else:
                        verification.finder_confirmation = True
                        if verification.owner_confirmation:
                            verification.verification_status = 'verified'
                    
                    if verification.verification_status == 'verified':
                        # Update item statuses
                        verification.lost_item.is_resolved = True
                        verification.found_item.is_resolved = True
                        system_msg = LostFoundChat(
                            verification=verification,
                            message="Item successfully verified. You can now exchange contact details to arrange for the return.",
                            is_system=True
                        )
                    else:
                        system_msg = LostFoundChat(
                            verification=verification,
                            message="Thank you for confirming. Waiting for the other party to verify as well.",
                            is_system=True
                        )
                else:
                    verification.verification_status = 'rejected'
                    system_msg = LostFoundChat(
                        verification=verification,
                        message="It seems like this is not your item. You can continue searching for your lost item, or report it again.",
                        is_system=True
                    )
                db.session.add(system_msg)
            
            db.session.commit()
            return redirect(url_for('verification.chat', verification_id=verification.id))

    return render_template('verification/verify.html',
                         item=item,
                         item_type=item_type,
                         potential_matches=potential_matches,
                         verification=verification)

@verification_bp.route('/chat/<int:verification_id>', methods=['GET', 'POST'])
@login_required
def chat(verification_id):
    """Handle the verification chat interface."""
    verification = ItemVerification.query.get_or_404(verification_id)
    
    # Check if user is authorized
    if current_user.id not in [verification.lost_item.user_id, verification.found_item.user_id]:
        flash('You are not authorized to view this chat.', 'error')
        return redirect(url_for('lost_found.index'))
    
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            chat_msg = LostFoundChat(
                verification=verification,
                sender=current_user,
                message=message
            )
            db.session.add(chat_msg)
            db.session.commit()
    
    messages = LostFoundChat.query.filter_by(verification_id=verification_id).order_by(LostFoundChat.created_at).all()
    return render_template('verification/chat.html',
                         verification=verification,
                         messages=messages)
