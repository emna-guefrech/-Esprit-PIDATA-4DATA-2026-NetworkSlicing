"""
Configuration management for Flask application
Supports multiple environments: development, production, testing
"""
import os
from datetime import timedelta

class BaseConfig:
    """Base configuration shared across all environments"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = False  # Set to True in production with HTTPS
    
    # JSON
    JSON_SORT_KEYS = False
    JSON_PRETTY_PRINT = True
    
    # Application metadata
    APP_NAME = 'Network Slicing Dashboard'
    APP_VERSION = '1.0.0'


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    
    # Database - MYSQL
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DEV_DATABASE_URL',
        'mysql+pymysql://root:password@127.0.0.1:3306/network_slicing'
    )
    SQLALCHEMY_ECHO = True  # Log SQL queries
    # Keep pool settings for MySQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20,
    }
    
    # Email
    MAIL_DEBUG = True
    MAIL_SUPPRESS_SEND = False
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 1025))  # MailHog default
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@localhost')
    
    # Session
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    
    # Database - MYSQL
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_ECHO = False
    # Keep pool settings for MySQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20,
    }
    
    # Email
    MAIL_DEBUG = False
    MAIL_SUPPRESS_SEND = False
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@networkslicing.com')
    
    # Session
    SESSION_COOKIE_SECURE = True


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    
    # Use SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    
    # SQLite doesn't support pool settings, use minimal config
    SQLALCHEMY_ENGINE_OPTIONS = {}
    
    # Disable CSRF for easier testing
    WTF_CSRF_ENABLED = False
    
    # Email
    MAIL_SUPPRESS_SEND = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
