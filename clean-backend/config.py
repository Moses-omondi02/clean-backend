import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'agri-smart-detect-secret-key-2024'
    # Use DATABASE_URL from environment, fallback to SQLite in instance folder
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-agri-smart-detect'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)

    # CORS Configuration
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://agri-smart-detect.onrender.com",
        "https://agri-smart-detect-frontend.onrender.com"
    ]

    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    # SendGrid Configuration
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    SENDGRID_FROM_EMAIL = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@agri-smart-detect.com')
    APP_NAME = 'Agri Smart Detect'

    # Plant.id API Configuration
    PLANT_ID_API_KEY = os.environ.get('PLANT_ID_API_KEY')
    PLANT_ID_API_URL = 'https://api.plant.id/v2/identify'

    # Frontend URL for email links
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://agri-smart-detect.onrender.com')


class ProductionConfig(Config):
    """Production configuration for Render deployment"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    # Database must be provided via DATABASE_URL in production
    def __init__(self):
        super().__init__()
        uri = os.environ.get('DATABASE_URL')
        if not uri:
            raise ValueError("DATABASE_URL environment variable is required for production")
        self.SQLALCHEMY_DATABASE_URI = uri


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False