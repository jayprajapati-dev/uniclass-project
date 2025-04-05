from app import create_app
from models import db, Department

def init_departments():
    app = create_app()
    with app.app_context():
        # Check if departments already exist
        if Department.query.first() is None:
            # Default departments
            departments = [
                {
                    'name': 'Information Technology',
                    'code': 'IT',
                    'description': 'Department of Information Technology',
                    'is_active': True
                },
                {
                    'name': 'Civil Engineering',
                    'code': 'CIVIL',
                    'description': 'Department of Civil Engineering',
                    'is_active': True
                },
                {
                    'name': 'Mechanical Engineering',
                    'code': 'MECH',
                    'description': 'Department of Mechanical Engineering',
                    'is_active': True
                },
                {
                    'name': 'Electrical Engineering',
                    'code': 'EE',
                    'description': 'Department of Electrical Engineering',
                    'is_active': True
                },
                {
                    'name': 'Electronics & Communication Engineering',
                    'code': 'EC',
                    'description': 'Department of Electronics & Communication Engineering',
                    'is_active': True
                },
                {
                    'name': 'Information and Communication Technology',
                    'code': 'ICT',
                    'description': 'Department of Information and Communication Technology',
                    'is_active': True
                }
            ]

            # Add departments to database
            for dept_data in departments:
                department = Department(**dept_data)
                db.session.add(department)

            try:
                db.session.commit()
                print("Default departments initialized successfully!")
            except Exception as e:
                db.session.rollback()
                print(f"Error initializing departments: {str(e)}")
        else:
            print("Departments already exist in the database.")

if __name__ == '__main__':
    init_departments() 