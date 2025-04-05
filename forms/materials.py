from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SelectField, IntegerField
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