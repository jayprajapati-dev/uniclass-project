from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from models import db, MarketplaceListing, ListingImage, MarketplacePurchase, MarketplaceReview, ListingReport, User, Subject
from marketplace_forms import ListingForm, SearchForm, PurchaseForm, ReviewForm, ReportForm, MessageForm
from utils import save_image

marketplace = Blueprint('marketplace', __name__)

@marketplace.route('/marketplace')
def index():
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Get filter parameters
    department = request.args.get('department', 'all')
    semester = request.args.get('semester', 'all')
    subject = request.args.get('subject', 'all')
    category = request.args.get('category', 'all')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    condition = request.args.get('condition', 'all')
    sort_by = request.args.get('sort_by', 'newest')
    query = request.args.get('query', '')
    
    # Build query
    listings_query = MarketplaceListing.query.filter_by(status='available')
    
    # Apply filters
    if department != 'all':
        listings_query = listings_query.filter_by(department=department)
    if semester != 'all':
        listings_query = listings_query.filter_by(semester=int(semester))
    if subject != 'all':
        listings_query = listings_query.filter_by(subject_id=int(subject))
    if category != 'all':
        listings_query = listings_query.filter_by(category=category)
    if min_price is not None:
        listings_query = listings_query.filter(MarketplaceListing.price >= min_price)
    if max_price is not None:
        listings_query = listings_query.filter(MarketplaceListing.price <= max_price)
    if condition != 'all':
        listings_query = listings_query.filter_by(condition=condition)
    if query:
        listings_query = listings_query.filter(
            (MarketplaceListing.title.ilike(f'%{query}%')) |
            (MarketplaceListing.description.ilike(f'%{query}%'))
        )
    
    # Sort results
    if sort_by == 'price_low':
        listings_query = listings_query.order_by(MarketplaceListing.price.asc())
    elif sort_by == 'price_high':
        listings_query = listings_query.order_by(MarketplaceListing.price.desc())
    else:
        listings_query = listings_query.order_by(MarketplaceListing.created_at.desc())
    
    # Get available subjects based on current filters
    available_subjects = Subject.query
    if department != 'all':
        available_subjects = available_subjects.filter_by(department=department)
    if semester != 'all':
        available_subjects = available_subjects.filter_by(semester=int(semester))
    available_subjects = available_subjects.all()
    
    listings = listings_query.paginate(page=page, per_page=per_page)
    
    return render_template('marketplace/index.html', 
                         listings=listings, 
                         form=form,
                         available_subjects=available_subjects)

@marketplace.route('/marketplace/create', methods=['GET', 'POST'])
@login_required
def create_listing():
    form = ListingForm()
    if form.validate_on_submit():
        listing = MarketplaceListing(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            price=form.price.data,
            is_negotiable=form.is_negotiable.data,
            condition=form.condition.data,
            pickup_location=form.pickup_location.data,
            contact_preference=form.contact_preference.data,
            seller_id=current_user.id
        )
        
        db.session.add(listing)
        db.session.commit()
        
        # Handle image uploads
        if form.images.data:
            for image in form.images.data:
                if image:
                    filename = secure_filename(image.filename)
                    image_path = save_image(image, 'marketplace')
                    listing_image = ListingImage(
                        listing_id=listing.id,
                        image_path=image_path,
                        is_primary=(listing.images.count() == 0)
                    )
                    db.session.add(listing_image)
        
        db.session.commit()
        flash('Listing created successfully!', 'success')
        return redirect(url_for('marketplace.listing', id=listing.id))
    
    return render_template('marketplace/create.html', form=form)

@marketplace.route('/marketplace/listing/<int:id>')
def listing(id):
    listing = MarketplaceListing.query.get_or_404(id)
    form = MessageForm()
    return render_template('marketplace/listing.html', listing=listing, form=form)

@marketplace.route('/marketplace/listing/<int:id>/purchase', methods=['GET', 'POST'])
@login_required
def purchase_listing(id):
    listing = MarketplaceListing.query.get_or_404(id)
    if listing.seller_id == current_user.id:
        flash('You cannot purchase your own listing!', 'error')
        return redirect(url_for('marketplace.listing', id=id))
    
    form = PurchaseForm()
    if form.validate_on_submit():
        purchase = MarketplacePurchase(
            listing_id=listing.id,
            buyer_id=current_user.id,
            seller_id=listing.seller_id,
            price=listing.price,
            payment_method=form.payment_method.data,
            meetup_location=form.meetup_location.data,
            meetup_time=form.meetup_time.data
        )
        
        listing.status = 'reserved'
        db.session.add(purchase)
        db.session.commit()
        
        flash('Purchase request sent successfully!', 'success')
        return redirect(url_for('marketplace.purchase', id=purchase.id))
    
    return render_template('marketplace/purchase.html', listing=listing, form=form)

@marketplace.route('/marketplace/purchase/<int:id>')
@login_required
def purchase(id):
    purchase = MarketplacePurchase.query.get_or_404(id)
    if purchase.buyer_id != current_user.id and purchase.seller_id != current_user.id:
        flash('You are not authorized to view this purchase!', 'error')
        return redirect(url_for('marketplace.index'))
    
    return render_template('marketplace/purchase_details.html', purchase=purchase)

@marketplace.route('/marketplace/purchase/<int:id>/complete', methods=['POST'])
@login_required
def complete_purchase(id):
    purchase = MarketplacePurchase.query.get_or_404(id)
    if purchase.seller_id != current_user.id:
        flash('You are not authorized to complete this purchase!', 'error')
        return redirect(url_for('marketplace.index'))
    
    purchase.status = 'completed'
    purchase.payment_status = 'completed'
    purchase.completed_at = datetime.utcnow()
    purchase.listing.status = 'sold'
    
    db.session.commit()
    flash('Purchase marked as completed!', 'success')
    return redirect(url_for('marketplace.purchase', id=id))

@marketplace.route('/marketplace/listing/<int:id>/review', methods=['GET', 'POST'])
@login_required
def review_listing(id):
    listing = MarketplaceListing.query.get_or_404(id)
    purchase = MarketplacePurchase.query.filter_by(
        listing_id=listing.id,
        buyer_id=current_user.id,
        status='completed'
    ).first()
    
    if not purchase:
        flash('You can only review listings you have purchased!', 'error')
        return redirect(url_for('marketplace.listing', id=id))
    
    form = ReviewForm()
    if form.validate_on_submit():
        review = MarketplaceReview(
            listing_id=listing.id,
            reviewer_id=current_user.id,
            reviewee_id=listing.seller_id,
            rating=form.rating.data,
            review=form.review.data,
            communication_rating=form.communication_rating.data,
            item_condition_rating=form.item_condition_rating.data
        )
        
        db.session.add(review)
        
        # Update seller's rating
        seller = User.query.get(listing.seller_id)
        seller.total_ratings += 1
        seller.rating = (seller.rating * (seller.total_ratings - 1) + form.rating.data) / seller.total_ratings
        
        db.session.commit()
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('marketplace.listing', id=id))
    
    return render_template('marketplace/review.html', listing=listing, form=form)

@marketplace.route('/marketplace/listing/<int:id>/report', methods=['GET', 'POST'])
@login_required
def report_listing(id):
    listing = MarketplaceListing.query.get_or_404(id)
    form = ReportForm()
    
    if form.validate_on_submit():
        report = ListingReport(
            listing_id=listing.id,
            reporter_id=current_user.id,
            reason=form.reason.data,
            description=form.description.data
        )
        
        db.session.add(report)
        db.session.commit()
        
        flash('Report submitted successfully!', 'success')
        return redirect(url_for('marketplace.listing', id=id))
    
    return render_template('marketplace/report.html', listing=listing, form=form)

@marketplace.route('/marketplace/messages')
@login_required
def messages():
    # Get all unique conversations
    sent_messages = db.session.query(MarketplacePurchase).filter(
        (MarketplacePurchase.buyer_id == current_user.id) |
        (MarketplacePurchase.seller_id == current_user.id)
    ).all()
    
    return render_template('marketplace/messages.html', conversations=sent_messages)

@marketplace.route('/marketplace/messages/<int:id>', methods=['GET', 'POST'])
@login_required
def conversation(id):
    purchase = MarketplacePurchase.query.get_or_404(id)
    if purchase.buyer_id != current_user.id and purchase.seller_id != current_user.id:
        flash('You are not authorized to view this conversation!', 'error')
        return redirect(url_for('marketplace.messages'))
    
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(
            sender_id=current_user.id,
            receiver_id=purchase.seller_id if current_user.id == purchase.buyer_id else purchase.buyer_id,
            content=form.message.data,
            item_id=purchase.listing_id,
            item_type='marketplace'
        )
        
        db.session.add(message)
        db.session.commit()
        
        return redirect(url_for('marketplace.conversation', id=id))
    
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == purchase.seller_id)) |
        ((Message.sender_id == purchase.seller_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    return render_template('marketplace/conversation.html', purchase=purchase, messages=messages, form=form)

@marketplace.route('/marketplace/get-subjects')
def get_subjects():
    department = request.args.get('department')
    semester = request.args.get('semester')
    
    if not department or not semester or department == 'all' or semester == 'all':
        return jsonify({'subjects': []})
    
    subjects = Subject.query.filter_by(
        department=department,
        semester=int(semester)
    ).all()
    
    return jsonify({
        'subjects': [{
            'id': subject.id,
            'name': subject.name
        } for subject in subjects]
    }) 