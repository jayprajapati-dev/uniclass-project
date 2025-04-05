# UniClass - Student Information Portal

  A comprehensive student information portal built with Flask.

## Features

- User authentication and authorization
- Student and admin dashboards
- Classroom management
- Timetable management
- Assignment submission and grading
- Study materials sharing
- Lost and found items
- Email notifications
- Reports generation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jayprajapati-dev/uniclass.git
cd uniclass
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Database Configuration
DATABASE_URL=sqlite:///app.db

# Email Configuration (for Flask-Mail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB max file size
```

5. Initialize the database:
```bash
python init_db.py
```

6. Create an admin user:
```bash
python create_admin.py
```

7. Run the application:
```bash
python app.py
```

## Usage

1. Access the application at `http://localhost:5000`
2. Login with your credentials
3. Navigate through different sections using the navigation menu

## Features in Detail

### User Management
- User registration and login
- Role-based access control (Admin, Student)
- Profile management

### Classroom Management
- Create and manage classrooms
- Assign teachers and students
- Track attendance

### Timetable Management
- Create and manage class schedules
- View timetable by class or teacher
- Conflict detection

### Assignment Management
- Create and assign homework
- Submit assignments
- Grade submissions
- Track deadlines

### Study Materials
- Upload and share study materials
- Organize by subject and class
- Download and view materials

### Lost and Found
- Report lost items
- List found items
- Track item status

### Email Notifications
- System notifications
- Assignment reminders
- Important announcements
- Custom notifications for different user groups

### Reports
- Generate various reports
- Export to Excel format
- Track user activity
- Monitor system usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please contact:
- Email: uddan1711@gmail.com

## Acknowledgments

- Flask documentation and community
- SQLAlchemy documentation
- All contributors and maintainers
