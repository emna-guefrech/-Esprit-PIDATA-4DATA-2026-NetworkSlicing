"""
Flask extensions initialization
These are instantiated here and initialized with app in the app factory
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

# SQLAlchemy ORM
db = SQLAlchemy()

# Flask-Login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Redirect to login when @login_required fails
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

# Flask-Mail
mail = Mail()
