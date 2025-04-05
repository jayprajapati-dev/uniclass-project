from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, BooleanField, SelectField, DateTimeField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
import os

class ListingForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('books', 'Books'),
        ('notes', 'Notes'),
        ('lab_equipment', 'Lab Equipment'),
        ('gadgets', 'Gadgets'),
        ('stationery', 'Stationery'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    is_negotiable = BooleanField('Price is Negotiable')
    condition = SelectField('Condition', choices=[
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], validators=[DataRequired()])
    pickup_location = StringField('Pickup Location', validators=[DataRequired(), Length(max=200)])
    contact_preference = SelectField('Contact Preference', choices=[
        ('in_app', 'In-App Chat'),
        ('whatsapp', 'WhatsApp'),
        ('phone', 'Phone Call')
    ], validators=[DataRequired()])
    images = FileField('Images', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPEG and PNG images are allowed!'),
        Optional()
    ])

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    category = SelectField('Category', choices=[
        ('all', 'All Categories'),
        ('books', 'Books'),
        ('notes', 'Notes'),
        ('lab_equipment', 'Lab Equipment'),
        ('gadgets', 'Gadgets'),
        ('stationery', 'Stationery'),
        ('other', 'Other')
    ], validators=[Optional()])
    min_price = FloatField('Min Price', validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField('Max Price', validators=[Optional(), NumberRange(min=0)])
    condition = SelectField('Condition', choices=[
        ('all', 'All Conditions'),
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], validators=[Optional()])
    sort_by = SelectField('Sort By', choices=[
        ('newest', 'Newest First'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low')
    ], validators=[Optional()])

class PurchaseForm(FlaskForm):
    payment_method = SelectField('Payment Method', choices=[
        ('cash', 'Cash'),
        ('upi', 'UPI')
    ], validators=[DataRequired()])
    meetup_location = StringField('Meetup Location', validators=[DataRequired(), Length(max=200)])
    meetup_time = DateTimeField('Meetup Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])

class ReviewForm(FlaskForm):
    rating = IntegerField('Overall Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    review = TextAreaField('Review', validators=[Optional()])
    communication_rating = IntegerField('Communication Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    item_condition_rating = IntegerField('Item Condition Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])

class ReportForm(FlaskForm):
    reason = SelectField('Reason', choices=[
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('fake', 'Fake Listing'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])

class MessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired()])

class DepartmentForm(FlaskForm):
    code = StringField('Department Code', validators=[
        DataRequired(),
        Length(min=2, max=10)
    ])
    name = StringField('Department Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    description = TextAreaField('Description')
    is_active = BooleanField('Active')
    submit = SubmitField('Save Department') 