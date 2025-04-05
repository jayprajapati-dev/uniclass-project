from app import app, db
from models import AdminRole
import json

def init_admin_roles():
    # Define all admin roles with their permissions
    roles = [
        # Classroom Management Roles
        {
            'name': 'Classroom Manager',
            'module': 'classroom',
            'permissions': json.dumps({
                'add_classroom': True,
                'edit_classroom': True,
                'delete_classroom': True,
                'update_availability': True
            }),
            'description': 'Manages classroom data and real-time availability'
        },
        {
            'name': 'Booking Approver',
            'module': 'classroom',
            'permissions': json.dumps({
                'approve_booking': True,
                'reject_booking': True,
                'view_bookings': True
            }),
            'description': 'Handles student classroom booking requests'
        },
        
        # Study Materials Roles
        {
            'name': 'Content Moderator',
            'module': 'materials',
            'permissions': json.dumps({
                'approve_listing': True,
                'reject_listing': True,
                'remove_listing': True,
                'view_all_listings': True
            }),
            'description': 'Reviews and approves book/material listings'
        },
        {
            'name': 'Finance Admin',
            'module': 'materials',
            'permissions': json.dumps({
                'manage_payments': True,
                'handle_disputes': True,
                'issue_refunds': True
            }),
            'description': 'Handles payment disputes and financial matters'
        },
        
        # Lost & Found Roles
        {
            'name': 'Lost Found Moderator',
            'module': 'lost_found',
            'permissions': json.dumps({
                'approve_post': True,
                'remove_post': True,
                'manage_claims': True
            }),
            'description': 'Approves and manages lost/found posts'
        },
        {
            'name': 'User Support Admin',
            'module': 'lost_found',
            'permissions': json.dumps({
                'handle_disputes': True,
                'manage_reports': True,
                'contact_users': True
            }),
            'description': 'Handles user disputes and fraud reports'
        },
        
        # Assignment Roles
        {
            'name': 'Assignment Manager',
            'module': 'assignments',
            'permissions': json.dumps({
                'create_assignment': True,
                'edit_assignment': True,
                'delete_assignment': True,
                'manage_deadlines': True
            }),
            'description': 'Uploads assignments and manages deadlines'
        },
        {
            'name': 'Grading Admin',
            'module': 'assignments',
            'permissions': json.dumps({
                'grade_submission': True,
                'provide_feedback': True,
                'manage_extensions': True
            }),
            'description': 'Reviews submissions and assigns grades'
        },
        
        # Timetable Roles
        {
            'name': 'Timetable Manager',
            'module': 'timetable',
            'permissions': json.dumps({
                'generate_timetable': True,
                'edit_timetable': True,
                'manage_schedules': True
            }),
            'description': 'Creates and updates class schedules'
        },
        {
            'name': 'Issue Resolution Admin',
            'module': 'timetable',
            'permissions': json.dumps({
                'handle_complaints': True,
                'resolve_conflicts': True,
                'update_students': True
            }),
            'description': 'Handles scheduling issues and student complaints'
        },
        {
            'name': 'AI Schedule Moderator',
            'module': 'timetable',
            'permissions': json.dumps({
                'oversee_ai': True,
                'adjust_parameters': True,
                'validate_schedules': True
            }),
            'description': 'Oversees AI-generated schedules and ensures accuracy'
        },
        
        # Quiz Roles
        {
            'name': 'Quiz Manager',
            'module': 'quiz',
            'permissions': json.dumps({
                'create_quiz': True,
                'edit_quiz': True,
                'set_difficulty': True,
                'manage_categories': True
            }),
            'description': 'Manages quiz content and difficulty levels'
        },
        {
            'name': 'Leaderboard Admin',
            'module': 'quiz',
            'permissions': json.dumps({
                'manage_leaderboard': True,
                'remove_cheaters': True,
                'adjust_scores': True
            }),
            'description': 'Ensures leaderboard fairness and removes cheaters'
        },
        {
            'name': 'AI Quiz Moderator',
            'module': 'quiz',
            'permissions': json.dumps({
                'oversee_generation': True,
                'filter_content': True,
                'adjust_ai_params': True
            }),
            'description': 'Oversees AI-generated quizzes and filters content'
        }
    ]
    
    # Create roles in database
    for role_data in roles:
        role = AdminRole.query.filter_by(name=role_data['name']).first()
        if not role:
            role = AdminRole(**role_data)
            db.session.add(role)
    
    db.session.commit()
    print("Admin roles initialized successfully!")

if __name__ == '__main__':
    with app.app_context():
        init_admin_roles()
