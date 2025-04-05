from datetime import datetime
from models import db

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
    
    # User relationships
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reporter = db.relationship('User', backref='reported_items')
    claimer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    claimer = db.relationship('User', backref='claimed_items')
    
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