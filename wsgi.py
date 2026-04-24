"""
WSGI application entry point for production
Use this with production servers like Gunicorn or uWSGI
Example: gunicorn wsgi:app
"""
import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment (default to production)
config_name = os.getenv('FLASK_ENV', 'production')

app = create_app(config_name)

if __name__ == '__main__':
    # This is only for local testing, use Gunicorn for production
    app.run(debug=False)
