from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import logging

db = SQLAlchemy()

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    from config import config_by_name
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    from app.routes import api_bp, web_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(web_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app


def setup_logging(app):
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.setLevel(logging.INFO)
