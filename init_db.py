import os
from app import app, db
from models import User, AdminRole, UserRole, Report, Assignment, AssignmentSubmission, LostItem, FoundItem, ItemVerification, LostFoundChat, Feedback, Message, StudyMaterial, Classroom, TimeSlot, Subject, TimetableEntry

def init_database():
    # Ensure instance directory exists with proper permissions
    instance_dir = os.path.join(os.getcwd(), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    print(f"Created instance directory at: {instance_dir}")
    
    # Delete existing database file if it exists
    db_path = os.path.join(instance_dir, 'uniclass.db')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Removed existing database file")
        except Exception as e:
            print(f"Error removing database file: {e}")
            return

    with app.app_context():
        try:
            # Drop all tables first
            db.drop_all()
            print("Dropped all existing tables")
            
            # Create all tables
            db.create_all()
            print("Created all tables")
            
            # Create admin user
            admin = User(
                username='admin',
                email='prajapatijay17112007@gmail.com',
                is_admin=True,
                is_approved=True,
                role='admin'
            )
            admin.set_password('altogmax1')
            db.session.add(admin)
            db.session.commit()
            print("Created admin user")
            
            # Create default admin role
            admin_role = AdminRole(
                name='Super Admin',
                module='all',
                permissions='["all"]',
                description='Super administrator with full access'
            )
            db.session.add(admin_role)
            db.session.commit()
            print("Created default admin role")
            
            # Assign admin role to admin user
            user_role = UserRole(user_id=admin.id, role_id=admin_role.id)
            db.session.add(user_role)
            db.session.commit()
            print("Assigned admin role to admin user")
            
            # Verify the admin user exists with all required columns
            admin_user = User.query.filter_by(email='prajapatijay17112007@gmail.com').first()
            if admin_user:
                print("Admin user verified with all columns:")
                print(f"ID: {admin_user.id}")
                print(f"Username: {admin_user.username}")
                print(f"Email: {admin_user.email}")
                print(f"Is Admin: {admin_user.is_admin}")
                print(f"Is Approved: {admin_user.is_approved}")
                print(f"Role: {admin_user.role}")
                
                # Verify the database connection
                try:
                    db.session.execute("SELECT * FROM user")
                    print("Database connection verified")
                except Exception as e:
                    print(f"Database connection error: {e}")
            else:
                print("Warning: Admin user not found after creation")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            db.session.rollback()
            return

if __name__ == '__main__':
    init_database()
