#!/usr/bin/env python
"""
Quick validation test for Network Slicing Dashboard
Checks if all imports work and basic app can start
Run: python check_setup.py
"""

import sys
import os

def check_imports():
    """Check all imports work"""
    try:
        print("✓ Checking Python imports...")
        
        # Flask imports
        from flask import Flask, render_template, request
        print("  ✓ Flask")
        
        # SQLAlchemy
        from flask_sqlalchemy import SQLAlchemy
        print("  ✓ Flask-SQLAlchemy")
        
        # Flask-Login
        from flask_login import LoginManager, login_required
        print("  ✓ Flask-Login")
        
        # Werkzeug
        from werkzeug.security import generate_password_hash, check_password_hash
        print("  ✓ Werkzeug (password hashing)")
        
        # Local app imports
        sys.path.insert(0, os.path.dirname(__file__))
        from app import create_app
        print("  ✓ App factory (create_app)")
        
        from app.extensions import db, login_manager, mail
        print("  ✓ Extensions (db, login_manager, mail)")
        
        from app.models.user import User, UserRole
        print("  ✓ User model & UserRole")
        
        from app.models.monitoring import Alert, Threshold, Prediction
        print("  ✓ Monitoring models")
        
        from app.security import role_required, admin_required
        print("  ✓ Security decorators")
        
        from app.blueprints.auth import auth_bp
        print("  ✓ Auth blueprint")
        
        from app.blueprints.dashboard import dashboard_bp
        print("  ✓ Dashboard blueprint")
        
        from app.blueprints.admin import admin_bp
        print("  ✓ Admin blueprint")
        
        return True
        
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False


def check_app_creation():
    """Check if app can be created"""
    try:
        print("\n✓ Creating Flask app...")
        
        from app import create_app
        
        # Try creating app in test mode
        app = create_app('testing')
        print("  ✓ App created in testing mode")
        
        # Check blueprints registered
        if 'auth' in app.blueprints:
            print("  ✓ Auth blueprint registered")
        if 'dashboard' in app.blueprints:
            print("  ✓ Dashboard blueprint registered")
        if 'admin' in app.blueprints:
            print("  ✓ Admin blueprint registered")
        
        return True
        
    except Exception as e:
        print(f"  ✗ App creation error: {e}")
        return False


def check_config():
    """Check configuration"""
    try:
        print("\n✓ Checking configuration...")
        
        from config import DevelopmentConfig, ProductionConfig, TestingConfig
        print("  ✓ Development config")
        print("  ✓ Production config")
        print("  ✓ Testing config")
        
        # Check required config values
        test_config = TestingConfig()
        required_attrs = ['DEBUG', 'TESTING', 'SQLALCHEMY_DATABASE_URI', 'SECRET_KEY']
        
        for attr in required_attrs:
            if hasattr(test_config, attr):
                print(f"  ✓ Config has {attr}")
            else:
                print(f"  ✗ Config missing {attr}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False


def check_files():
    """Check required files exist"""
    try:
        print("\n✓ Checking required files...")
        
        required_files = [
            'config.py',
            'requirements.txt',
            '.env.example',
            'run.py',
            'wsgi.py',
            'app/__init__.py',
            'app/extensions.py',
            'app/security.py',
            'app/models/user.py',
            'app/models/monitoring.py',
            'app/models/logs.py',
            'app/blueprints/auth.py',
            'app/blueprints/dashboard.py',
            'app/blueprints/admin.py',
            'app/templates/base.html',
            'app/templates/auth/login.html',
            'app/templates/dashboard/index.html',
            'app/static/css/dashboard.css',
            'app/static/js/dashboard.js',
            'README.md',
            'STRUCTURE.md',
            'TEST_API.md',
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"  ✓ {file_path}")
            else:
                print(f"  ✗ {file_path} MISSING")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ File check error: {e}")
        return False


def main():
    """Run all checks"""
    print("=" * 60)
    print("Network Slicing Dashboard - Setup Validation")
    print("=" * 60)
    
    checks = [
        ("Imports", check_imports),
        ("Configuration", check_config),
        ("Files", check_files),
        ("App Creation", check_app_creation),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n✗ {check_name} failed: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ All checks passed! Project is ready to run.")
        print("\nNext steps:")
        print("1. Create .env file (copy from .env.example)")
        print("2. Update database credentials in .env")
        print("3. Create MySQL database and tables")
        print("4. Run: python run.py")
        print("5. Access: http://127.0.0.1:5000")
        return 0
    else:
        print("\n✗ Some checks failed. Please review errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
