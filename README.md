﻿# UniClass - Student Information Portal

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

## 🌟Features

### Core Features
- 🔐 User authentication and authorization
- 📊 Student and admin dashboards
- 🏫 Classroom management
- 📅 Timetable management
- 📝 Assignment submission and grading
- 📚 Study materials sharing
- 🔍 Lost and found items
- 📧 Email notifications
- 📊 Reports generation

### Detailed Features
#### User Management
- User registration and login
- Role-based access control (Admin, Student)
- Profile management
- Password reset functionality

#### Classroom Management
- Create and manage classrooms
- Assign teachers and students
- Track attendance
- Class announcements
- Student performance tracking

#### Timetable Management
- Create and manage class schedules
- View timetable by class or teacher
- Conflict detection
- Export timetable in various formats

#### Assignment Management
- Create and assign homework
- Submit assignments online
- Grade assignments
- Track submission deadlines
- Plagiarism detection

#### Study Materials
- Upload and share study materials
- Categorize materials by subject
- Search and filter materials
- Download materials

#### Lost and Found
- Report lost items
- Search found items
- Claim lost items
- Item categorization

## 📖 Usage Guide

### Accessing the Application
1. Open your web browser and navigate to `http://localhost:5000`
2. Login with your credentials
3. Navigate through different sections using the navigation menu

### User Roles

#### Admin
- Manage users and permissions
- Create and manage classrooms
- Generate reports
- Configure system settings

#### Student
- View timetable
- Submit assignments
- Access study materials
- Report lost items

## 🔧 Technical Details

### Tech Stack
- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- Email: Flask-Mail
- File Storage: Local file system

### Project Structure
```
uniclass/
├── app/
│   ├── static/
│   ├── templates/
│   ├── models/
│   ├── routes/
│   └── utils/
├── uploads/
├── venv/
├── .env
├── requirements.txt
├── app.py
├── init_db.py
└── create_admin.py

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
- Email: prajapatijay17112007@gmail.com

## Acknowledgments

- Flask documentation and community
- SQLAlchemy documentation
- All contributors and maintainers
