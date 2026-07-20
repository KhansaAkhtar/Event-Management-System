import os
from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')  or 'dev-secret-key-change-later'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-dev-secret-change-later'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or  'sqlite:///' +os.path.join (basedir, 'event_management.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False