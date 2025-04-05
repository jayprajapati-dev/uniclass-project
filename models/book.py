from datetime import datetime
from models import db

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    material_type = db.Column(db.String(50), nullable=False)  # Book, Notes, Question Papers, etc.
    branch = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(50), nullable=False)  # New, Like New, Good, Fair, Poor
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    seller = db.relationship('User', backref='books')
    
    def __repr__(self):
        return f'<Book {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'subject': self.subject,
            'material_type': self.material_type,
            'branch': self.branch,
            'semester': self.semester,
            'price': self.price,
            'condition': self.condition,
            'description': self.description,
            'image_path': self.image_path,
            'status': self.status,
            'seller_id': self.seller_id,
            'seller_name': self.seller.username,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        } 