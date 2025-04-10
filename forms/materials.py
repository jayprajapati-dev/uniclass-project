from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SelectField, IntegerField, FloatField
from wtforms.validators import DataRequired, Optional, NumberRange

class MaterialForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    department = SelectField('Branch', coerce=int, validators=[DataRequired()])
    semester = SelectField('Semester', coerce=int, validators=[DataRequired()])
    subject = SelectField('Subject', coerce=int, validators=[DataRequired()])
    type = SelectField('Type', choices=[
        ('notes', 'Notes'),
        ('books', 'Books'),
        ('papers', 'Question Papers'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    file = FileField('File', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])

class StudyMaterialForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    material_type = SelectField('Material Type', choices=[
        ('book', 'Book'),
        ('notes', 'Notes'),
        ('question_papers', 'Question Papers'),
        ('study_guide', 'Study Guide'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    branch = SelectField('Branch', choices=[
        ('computer', 'Computer Engineering'),
        ('mechanical', 'Mechanical Engineering'),
        ('civil', 'Civil Engineering'),
        ('electrical', 'Electrical Engineering'),
        ('electronics', 'Electronics Engineering')
    ], validators=[DataRequired()])
    semester = SelectField('Semester', choices=[
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6')
    ], validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    condition = SelectField('Condition', choices=[
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Image', validators=[Optional()]) 