from app import app, db
from models import User

def create_admin():
    with app.app_context():
        # Check if admin exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create new admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True,
            is_approved=True,
            role='admin'
        )
        admin.set_password('admin123')
        
        # Add to database
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully")

if __name__ == '__main__':
    create_admin() 