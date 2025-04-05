from app import app, db
from models import User, AdminRole, UserRole, Report, Assignment, AssignmentSubmission, LostItem, FoundItem, ItemVerification, LostFoundChat, Feedback, Message, StudyMaterial, MaterialCategory, MaterialDownload, MaterialView, Classroom, TimeSlot, Subject, TimetableEntry

def create_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True,
            is_approved=True,
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        print("Database and admin user created successfully!")

if __name__ == '__main__':
    create_database() 