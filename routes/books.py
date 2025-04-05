from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import db, Book
from datetime import datetime

books_bp = Blueprint('books', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@books_bp.route('/books')
def index():
    # Get filter parameters
    page = request.args.get('page', 1, type=int)
    branch = request.args.get('branch')
    semester = request.args.get('semester')
    material_type = request.args.get('material_type')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    search_query = request.args.get('search', '')
    
    # Build the query
    query = Book.query.filter_by(status='approved')
    
    if search_query:
        query = query.filter(
            (Book.title.ilike(f'%{search_query}%')) |
            (Book.subject.ilike(f'%{search_query}%')) |
            (Book.description.ilike(f'%{search_query}%'))
        )
    
    if branch:
        query = query.filter_by(branch=branch)
    if semester:
        query = query.filter_by(semester=semester)
    if material_type:
        query = query.filter_by(material_type=material_type)
    if min_price is not None:
        query = query.filter(Book.price >= min_price)
    if max_price is not None:
        query = query.filter(Book.price <= max_price)
    
    books = query.order_by(Book.created_at.desc()).paginate(page=page, per_page=12)
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'books': [book.to_dict() for book in books.items],
            'has_next': books.has_next,
            'has_prev': books.has_prev,
            'next_num': books.next_num,
            'prev_num': books.prev_num
        })
    
    return render_template('books/index.html', books=books)

@books_bp.route('/books/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        title = request.form.get('title')
        subject = request.form.get('subject')
        material_type = request.form.get('material_type')
        branch = request.form.get('branch')
        semester = request.form.get('semester')
        price = request.form.get('price')
        condition = request.form.get('condition')
        description = request.form.get('description')
        
        if not all([title, subject, material_type, branch, semester, price, condition, description]):
            flash('All fields are required', 'error')
            return redirect(request.url)
        
        book = Book(
            title=title,
            subject=subject,
            material_type=material_type,
            branch=branch,
            semester=int(semester),
            price=float(price),
            condition=condition,
            description=description,
            seller_id=current_user.id
        )
        
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                book.image_path = filename
        
        db.session.add(book)
        db.session.commit()
        flash('Your listing has been submitted for approval', 'success')
        return redirect(url_for('books.index'))
    
    return render_template('books/new.html')

@books_bp.route('/books/<int:id>')
def show(id):
    book = Book.query.get_or_404(id)
    return render_template('books/show.html', book=book)

@books_bp.route('/books/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    book = Book.query.get_or_404(id)
    if book.seller_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to edit this listing', 'error')
        return redirect(url_for('books.show', id=id))
    
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.subject = request.form.get('subject')
        book.material_type = request.form.get('material_type')
        book.branch = request.form.get('branch')
        book.semester = int(request.form.get('semester'))
        book.price = float(request.form.get('price'))
        book.condition = request.form.get('condition')
        book.description = request.form.get('description')
        
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                book.image_path = filename
        
        db.session.commit()
        flash('Listing updated successfully', 'success')
        return redirect(url_for('books.show', id=id))
    
    return render_template('books/edit.html', book=book)

@books_bp.route('/books/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    book = Book.query.get_or_404(id)
    if book.seller_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to delete this listing', 'error')
        return redirect(url_for('books.show', id=id))
    
    db.session.delete(book)
    db.session.commit()
    flash('Listing deleted successfully', 'success')
    return redirect(url_for('books.index'))

# Admin routes
@books_bp.route('/admin/books')
@login_required
def admin_index():
    if not current_user.is_admin:
        flash('You are not authorized to access this page', 'error')
        return redirect(url_for('books.index'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')
    books = Book.query.filter_by(status=status).order_by(Book.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('books/admin/index.html', books=books)

@books_bp.route('/admin/books/<int:id>/approve', methods=['POST'])
@login_required
def approve(id):
    if not current_user.is_admin:
        flash('You are not authorized to perform this action', 'error')
        return redirect(url_for('books.index'))
    
    book = Book.query.get_or_404(id)
    book.status = 'approved'
    db.session.commit()
    flash('Listing approved successfully', 'success')
    return redirect(url_for('books.admin_index'))

@books_bp.route('/admin/books/<int:id>/reject', methods=['POST'])
@login_required
def reject(id):
    if not current_user.is_admin:
        flash('You are not authorized to perform this action', 'error')
        return redirect(url_for('books.index'))
    
    book = Book.query.get_or_404(id)
    book.status = 'rejected'
    db.session.commit()
    flash('Listing rejected successfully', 'success')
    return redirect(url_for('books.admin_index')) 