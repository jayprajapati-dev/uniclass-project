from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
from extensions import db, login_manager

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Admin Role Models
class AdminRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    module = db.Column(db.String(50), nullable=False)  # e.g., 'classroom', 'materials', 'lost_found'
    permissions = db.Column(db.String(200), nullable=False)  # JSON string of permissions
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', secondary='user_roles', back_populates='roles')

    def __repr__(self):
        return f'<AdminRole {self.name}>'

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('admin_role.id'), primary_key=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)  # Made nullable initially
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(10), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='student')  # student, teacher, admin
    department = db.Column(db.String(100), nullable=True)  # Added department field
    year = db.Column(db.String(10), nullable=True)  # Added year field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)  # Added is_active field
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    notification_area = db.Column(db.String(100))
    
    # Relationships
    roles = db.relationship('AdminRole', secondary='user_roles', back_populates='users')
    lost_items = db.relationship('LostItem', backref='owner', lazy='dynamic', foreign_keys='LostItem.user_id')
    found_items = db.relationship('FoundItem', backref='finder', lazy='dynamic', foreign_keys='FoundItem.user_id')
    lost_found_sent_messages = db.relationship('LostFoundChat', backref='sender', foreign_keys='LostFoundChat.sender_id', lazy='dynamic')
    lost_found_received_messages = db.relationship('LostFoundChat', backref='receiver', foreign_keys='LostFoundChat.receiver_id', lazy='dynamic')
    found_by_items = db.relationship('LostItem', backref='found_by_user', lazy='dynamic', foreign_keys='LostItem.found_by')
    
    # Feedback relationships
    given_feedback = db.relationship('Feedback', backref='reviewer', foreign_keys='Feedback.reviewer_id', lazy='dynamic')
    received_feedback = db.relationship('Feedback', backref='reviewee', foreign_keys='Feedback.reviewee_id', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """Check if user has a specific role."""
        if role_name == self.role:  # Check basic role (student/teacher)
            return True
        return any(role.name == role_name for role in self.roles)  # Check admin roles
        
    def has_permission(self, module, permission):
        """Check if user has a specific permission in a module."""
        for role in self.roles:
            if role.module == module:
                permissions = json.loads(role.permissions)
                return permission in permissions
        return False

    @property
    def is_administrator(self):
        return self.role == 'admin' or self.is_admin == True
        
    @property
    def is_teacher(self):
        return self.role == 'teacher'
        
    @property
    def is_student(self):
        return self.role == 'student'

# Message Models
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    message_type = db.Column(db.String(20), default='text')  # text, image, file
    file_path = db.Column(db.String(200))  # For file attachments
    parent_id = db.Column(db.Integer, db.ForeignKey('message.id'))  # For reply threads
    item_id = db.Column(db.Integer)  # ID of the related item (lost/found)
    item_type = db.Column(db.String(10))  # Type of item (lost/found)
    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    # Define relationships here instead
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy='dynamic'))
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy='dynamic'))

# Feedback Model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, nullable=False)
    item_type = db.Column(db.String(10), nullable=False)  # 'lost' or 'found'
    
    # Who gave the feedback
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Who received the feedback
    reviewee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Specific ratings
    communication_rating = db.Column(db.Integer)  # 1-5 stars
    timeliness_rating = db.Column(db.Integer)    # 1-5 stars
    overall_rating = db.Column(db.Integer)       # 1-5 stars

# Timetable Models
class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entries = db.relationship('TimetableEntry', backref='timetable', lazy=True)
    creator = db.relationship('User', backref='created_timetables')

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    entries = db.relationship('TimetableEntry', backref='time_slot', lazy=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    batch = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    entries = db.relationship('TimetableEntry', backref='subject', lazy=True)

class TimetableEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetable.id'), nullable=False)
    day = db.Column(db.String(20), nullable=False)  # Monday, Tuesday, etc.
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    teacher_name = db.Column(db.String(100), nullable=True)  # Added teacher_name field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    classroom = db.relationship('Classroom', backref='timetable_entries')

# Report Model
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # e.g., 'academic', 'infrastructure', 'other'
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, resolved, dismissed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    department = db.Column(db.String(100), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)

    def __repr__(self):
        return f'<Report {self.title}>'

# Assignment Models
class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    submission_type = db.Column(db.String(20), default='digital')  # digital or manual
    file_path = db.Column(db.String(200))
    department = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy=True)

class AssignmentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(200))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    teacher_notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='submissions')

# Lost & Found Models
class LostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    date_lost = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    contact_info = db.Column(db.String(200))
    image_path = db.Column(db.String(200))
    status = db.Column(db.String(20), default='active')  # active, found, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    found_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    found_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    chat_messages = db.relationship('LostFoundChat', backref='lost_item', foreign_keys='LostFoundChat.lost_item_id', lazy='dynamic')
    verifications = db.relationship('ItemVerification', backref='lost_item', foreign_keys='ItemVerification.lost_item_id', lazy='dynamic')

class FoundItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    date_found = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    storage_location = db.Column(db.String(200))
    contact_info = db.Column(db.String(200))
    image_path = db.Column(db.String(200))
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    chat_messages = db.relationship('LostFoundChat', backref='found_item', foreign_keys='LostFoundChat.found_item_id', lazy='dynamic')
    verifications = db.relationship('ItemVerification', backref='found_item', foreign_keys='ItemVerification.found_item_id', lazy='dynamic')

# Association table for potential matches
potential_matches = db.Table('potential_matches',
    db.Column('lost_item_id', db.Integer, db.ForeignKey('lost_item.id'), primary_key=True),
    db.Column('found_item_id', db.Integer, db.ForeignKey('found_item.id'), primary_key=True),
    db.Column('match_score', db.Float),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class ItemVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_item.id'), nullable=False)
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_item.id'), nullable=False)
    owner_confirmation = db.Column(db.Boolean, default=False)
    finder_confirmation = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)

class LostFoundChat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_item.id'), nullable=False)
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_item.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # e.g., 'assignment', 'timetable', 'system'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(200))  # Optional link to related content

    def __repr__(self):
        return f'<Notification {self.id}>'

# Study Material Models
class StudyMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(50), nullable=False)
    material_type = db.Column(db.String(50), nullable=False)  # book, notes, question papers, etc.
    branch = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(20), nullable=False)  # new, like new, good, fair
    image_path = db.Column(db.String(200))
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, sold
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    seller = db.relationship('User', foreign_keys=[seller_id], backref='materials_for_sale')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_materials')
    reports = db.relationship('MaterialReport', backref='material', lazy=True)
    purchases = db.relationship('MaterialPurchase', backref='material', lazy=True)

class MaterialReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('study_material.id'), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # spam, inappropriate, duplicate, fraud
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, resolved, dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='material_reports')
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref='resolved_material_reports')

class MaterialPurchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('study_material.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref='material_purchases')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='material_sales')

# Smart Classroom Finder Models
class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    floor = db.Column(db.String(20), nullable=False)  # Floor number
    building = db.Column(db.String(50), nullable=False)  # Building name
    room_type = db.Column(db.String(20), nullable=False)  # lecture_room, lab_room, computer_room, working_room
    department = db.Column(db.String(100), nullable=False)  # Department name
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Classroom {self.room_number}>'

class RoomReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_type = db.Column(db.String(20), nullable=False)  # occupied, maintenance, other
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, resolved, dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class LostFoundItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='open')  # open, claimed, closed
    type = db.Column(db.String(10), nullable=False)  # lost, found
    image_path = db.Column(db.String(255))
    verification_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    verification_details = db.Column(db.Text)
    
    # User relationships with explicit foreign keys
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reported_items')
    claimer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    claimer = db.relationship('User', foreign_keys=[claimer_id], backref='claimed_items')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LostFoundItem {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'location': self.location,
            'date': self.date.isoformat(),
            'status': self.status,
            'type': self.type,
            'image_path': self.image_path,
            'verification_status': self.verification_status,
            'reporter_id': self.reporter_id,
            'claimer_id': self.claimer_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
