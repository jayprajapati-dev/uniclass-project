from app import app, db
from models import User, AdminRole, UserRole, Report, Assignment, AssignmentSubmission, LostItem, FoundItem, ItemVerification, LostFoundChat, Feedback, Message, StudyMaterial, MaterialCategory, MaterialDownload, MaterialView, Classroom, TimeSlot, Subject, TimetableEntry

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        print("Database reset complete!")

if __name__ == '__main__':
    reset_database()
