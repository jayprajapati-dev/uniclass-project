from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateTimeField, IntegerField, BooleanField, FileField, TimeField, SubmitField, RadioField, FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, ValidationError, Regexp
from flask_wtf.file import FileAllowed, FileField
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = RadioField('Role', choices=[
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin')
    ], validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile Number', validators=[
        DataRequired(),
        Length(min=10, max=10, message='Mobile number must be 10 digits'),
        Regexp(r'^[0-9]+$', message='Mobile number must contain only digits')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('student', 'Student'),
        ('teacher', 'Teacher')
    ], validators=[DataRequired()])
    department = SelectField('Department', choices=[
        ('Civil Engineering', 'Civil Engineering (CE)'),
        ('Mechanical Engineering', 'Mechanical Engineering (ME)'),
        ('Electrical Engineering', 'Electrical Engineering (EE)'),
        ('Electronics & Communication Engineering', 'Electronics & Communication Engineering (EC)'),
        ('Computer Engineering', 'Computer Engineering (CE)'),
        ('Information Technology', 'Information Technology (IT)'),
        ('Information and Communication Technology', 'Information and Communication Technology (ICT)'),
        ('Automobile Engineering', 'Automobile Engineering'),
        ('Petroleum Engineering', 'Petroleum Engineering'),
        ('Architecture Engineering', 'Architecture Engineering'),
        ('Environmental Engineering', 'Environmental Engineering')
    ], validators=[DataRequired()])
    year = SelectField('Year', choices=[
        ('1', 'First Year'),
        ('2', 'Second Year'),
        ('3', 'Third Year'),
        ('4', 'Fourth Year')
    ], validators=[DataRequired()])

# New form for admin to add teachers
class AddTeacherForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    name = StringField('Full Name', validators=[DataRequired()])
    submit = SubmitField('Add Teacher')

class ClassroomForm(FlaskForm):
    room_number = StringField('Room Number', validators=[DataRequired()])
    room_type = SelectField('Room Type', choices=[
        ('lecture_room', 'Lecture Room'),
        ('lab_room', 'Lab Room'),
        ('computer_room', 'Computer Room'),
        ('working_room', 'Working Room (Teacher Office)')
    ], validators=[DataRequired()])
    building = StringField('Building Name', validators=[DataRequired()])
    floor = SelectField('Floor', choices=[
        ('GF', 'Ground Floor'),
        ('1F', '1st Floor'),
        ('2F', '2nd Floor'),
        ('3F', '3rd Floor')
    ], validators=[DataRequired()])
    department = SelectField('Department', choices=[
        ('CE', 'Civil Engineering (CE)'),
        ('ME', 'Mechanical Engineering (ME)'),
        ('EE', 'Electrical Engineering (EE)'),
        ('EC', 'Electronics & Communication Engineering (EC)'),
        ('IT', 'Information Technology (IT)'),
        ('ICT', 'Information and Communication Technology (ICT)')
    ], validators=[DataRequired()])
    location = StringField('Location Details', validators=[DataRequired()])
    submit = SubmitField('Save')

class ClassroomSearchForm(FlaskForm):
    search_query = StringField('Search Room Number', validators=[Optional()])
    room_type = SelectField('Room Type', choices=[
        ('', 'All Types'),
        ('lecture_room', 'Lecture Room'),
        ('lab_room', 'Lab Room'),
        ('computer_room', 'Computer Room'),
        ('working_room', 'Working Room (Teacher Office)')
    ])
    department = SelectField('Department', choices=[
        ('', 'All Departments'),
        ('CE', 'Civil Engineering (CE)'),
        ('ME', 'Mechanical Engineering (ME)'),
        ('EE', 'Electrical Engineering (EE)'),
        ('EC', 'Electronics & Communication Engineering (EC)'),
        ('IT', 'Information Technology (IT)'),
        ('ICT', 'Information and Communication Technology (ICT)')
    ])
    floor = SelectField('Floor', choices=[
        ('', 'All Floors'),
        ('GF', 'Ground Floor'),
        ('1F', '1st Floor'),
        ('2F', '2nd Floor'),
        ('3F', '3rd Floor')
    ])
    submit = SubmitField('Search')

class TimetableEntryForm(FlaskForm):
    classroom_id = SelectField('Classroom', coerce=int, validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=100)])
    faculty = StringField('Faculty', validators=[DataRequired(), Length(max=100)])
    batch = StringField('Batch', validators=[DataRequired(), Length(max=50)])
    day_of_week = SelectField('Day', choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday')
    ], validators=[DataRequired()])
    start_time = StringField('Start Time', validators=[DataRequired()])
    end_time = StringField('End Time', validators=[DataRequired()])

class AssignmentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    due_date = DateTimeField('Due Date', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    submission_type = SelectField('Submission Type', choices=[
        ('digital', 'Digital Submission'),
        ('manual', 'Manual Submission')
    ], validators=[DataRequired()])
    file = FileField('Assignment File', validators=[Optional()])

class AssignmentSubmissionForm(FlaskForm):
    file = FileField('Submission File', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    is_manual = BooleanField('Manual Submission')

class LostItemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    category = SelectField('Category', choices=[
        ('electronics', 'Electronics'),
        ('wallets', 'Wallets'),
        ('documents', 'Documents'),
        ('keys', 'Keys'),
        ('clothing', 'Clothing'),
        ('others', 'Others')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    date_lost = DateTimeField('Date Lost', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=200)])
    contact_info = StringField('Contact Information', validators=[DataRequired(), Length(max=200)])
    image = FileField('Image', validators=[Optional()])
    submit = SubmitField('Report Lost Item')

class FoundItemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    category = SelectField('Category', choices=[
        ('electronics', 'Electronics'),
        ('wallets', 'Wallets'),
        ('documents', 'Documents'),
        ('keys', 'Keys'),
        ('clothing', 'Clothing'),
        ('others', 'Others')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    date_found = DateTimeField('Date Found', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=200)])
    storage_location = StringField('Storage Location', validators=[DataRequired(), Length(max=200)])
    contact_info = StringField('Contact Information', validators=[DataRequired(), Length(max=200)])
    image = FileField('Image', validators=[Optional()])

class StudyMaterialForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=50)])
    material_type = SelectField('Material Type', choices=[
        ('book', 'Book'),
        ('notes', 'Notes'),
        ('question_papers', 'Question Papers'),
        ('study_guides', 'Study Guides'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    branch = SelectField('Branch', choices=[
        ('CE', 'Civil Engineering (CE)'),
        ('ME', 'Mechanical Engineering (ME)'),
        ('EE', 'Electrical Engineering (EE)'),
        ('EC', 'Electronics & Communication Engineering (EC)'),
        ('IT', 'Information Technology (IT)'),
        ('ICT', 'Information and Communication Technology (ICT)')
    ], validators=[DataRequired()])
    semester = SelectField('Semester', choices=[
        (1, '1st Semester'),
        (2, '2nd Semester'),
        (3, '3rd Semester'),
        (4, '4th Semester'),
        (5, '5th Semester'),
        (6, '6th Semester')

    ], coerce=int, validators=[DataRequired()])
    price = FloatField('Price (₹)', validators=[DataRequired(), NumberRange(min=0)])
    condition = SelectField('Condition', choices=[
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Material Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPEG and PNG images are allowed!')
    ])
    submit = SubmitField('List Material')

class MaterialSearchForm(FlaskForm):
    search_query = StringField('Search', validators=[Optional()])
    material_type = SelectField('Material Type', choices=[
        ('', 'All Types'),
        ('book', 'Book'),
        ('notes', 'Notes'),
        
        ('other', 'Other')
    ], validators=[Optional()])
    branch = SelectField('Branch', choices=[
        ('', 'All Branches'),
        ('CE', 'Civil Engineering (CE)'),
        ('ME', 'Mechanical Engineering (ME)'),
        ('EE', 'Electrical Engineering (EE)'),
        ('EC', 'Electronics & Communication Engineering (EC)'),
        ('IT', 'Information Technology (IT)'),
        ('ICT', 'Information and Communication Technology (ICT)')
    ], validators=[Optional()])
    semester = SelectField('Semester', choices=[
        ('', 'All Semesters'),
        ('1', '1st Semester'),
        ('2', '2nd Semester'),
        ('3', '3rd Semester'),
        ('4', '4th Semester'),
        ('5', '5th Semester'),
        ('6', '6th Semester')   
    ], validators=[Optional()])
    min_price = FloatField('Min Price', validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField('Max Price', validators=[Optional(), NumberRange(min=0)])
    condition = SelectField('Condition', choices=[
        ('', 'Any Condition'),
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair')
    ], validators=[Optional()])
    submit = SubmitField('Search')

class MaterialReportForm(FlaskForm):
    report_type = SelectField('Report Type', choices=[
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('duplicate', 'Duplicate Listing'),
        ('fraud', 'Fraudulent Listing'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit Report')

class TimetableForm(FlaskForm):
    semester = StringField('Semester', validators=[DataRequired()])
    year = StringField('Year', validators=[DataRequired()])
    department = SelectField('Department', choices=[
        ('Computer Science', 'Computer Science'),
        ('Electronics', 'Electronics'),
        ('Mechanical', 'Mechanical'),
        ('Civil', 'Civil'),
        ('Information Technology', 'Information Technology')
    ], validators=[DataRequired()])

class UserProfileForm(FlaskForm):
    email_notifications = BooleanField('Email Notifications')
    push_notifications = BooleanField('Push Notifications')
    sms_notifications = BooleanField('SMS Notifications')
    notification_area = StringField('Notification Area', validators=[Optional(), Length(max=100)]) 