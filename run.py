"""
Development server entry point
Usage: python run.py
"""
import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file FIRST
load_dotenv()

# Get configuration from environment or use default (development)
config_name = os.getenv('FLASK_ENV', 'development')

app = create_app(config_name)

if __name__ == '__main__':
    # Run development server
    # Set debug=True in config.py for development
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=app.config['DEBUG']
    )
