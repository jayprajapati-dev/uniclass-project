import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///uniclass.db'  # Change to MySQL in production
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    # Add production MySQL database URI here
    # SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/dbname'
