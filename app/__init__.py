"""
Application factory for Flask app
Creates and configures the Flask application instance
"""
import os
from dotenv import load_dotenv

# Load .env FIRST before importing config
load_dotenv()

from flask import Flask
from config import config
from app.extensions import db, login_manager, mail


def create_app(config_name='development'):
    """
    Create and configure the Flask application
    
    Args:
        config_name (str): Configuration name ('development', 'production', 'testing')
    
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config.get(config_name, config['default']))
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Create database tables (for development/testing)
    with app.app_context():
        db.create_all()
        
        # Initialize default admin user if none exist
        from app.init_db import init_default_users
        init_default_users()
    
    # Setup Flask-Login user loader
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return app
