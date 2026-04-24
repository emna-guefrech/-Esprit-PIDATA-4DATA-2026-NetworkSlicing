"""
Database initialization - Auto-create default admin user on startup
"""
from app.models.user import User
from app.extensions import db


def init_default_users():
    """
    Initialize default admin user if none exist
    Called on app startup
    """
    try:
        # Check if any admin user exists
        admin_exists = User.query.filter_by(role='system_admin').first()
        
        if not admin_exists:
            print("\n" + "="*60)
            print("📝 INITIALIZING DEFAULT ADMIN USER")
            print("="*60)
            
            # Create default admin user
            admin = User(
                username='admin',
                email='admin@network-slicing.local',
                role='system_admin'
            )
            admin.set_password('Admin@123456')  # Default password
            admin.email_verified = True  # Admin is auto-verified
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin user created!")
            print("   Username: admin")
            print("   Email: admin@network-slicing.local")
            print("   Password: Admin@123456")
            print("   ⚠️  CHANGE THESE CREDENTIALS AFTER FIRST LOGIN!")
            print("="*60 + "\n")
        else:
            print("✓ Admin user already exists")
            
    except Exception as e:
        print(f"⚠️  Could not initialize admin user: {e}")
        db.session.rollback()
