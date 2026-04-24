"""
User model - maps to existing 'users' table in MySQL
Includes password hashing, role management, and email verification
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db
import secrets
import string


class UserRole:
    """User role constants"""
    SYSTEM_ADMIN = 'system_admin'
    NETWORK_ENGINEER = 'network_engineer'
    DATA_SCIENTIST = 'data_scientist'
    NOC_OPERATOR = 'noc_operator'
    
    ALL_ROLES = [
        SYSTEM_ADMIN,
        NETWORK_ENGINEER,
        DATA_SCIENTIST,
        NOC_OPERATOR,
    ]
    
    ROLE_LABELS = {
        SYSTEM_ADMIN: 'System Administrator',
        NETWORK_ENGINEER: 'Network Engineer',
        DATA_SCIENTIST: 'Data Scientist',
        NOC_OPERATOR: 'NOC Operator',
    }
    
    @classmethod
    def is_valid(cls, role):
        """Check if role is valid"""
        return role in cls.ALL_ROLES
    
    @classmethod
    def get_label(cls, role):
        """Get display label for role"""
        return cls.ROLE_LABELS.get(role, role)


class User(UserMixin, db.Model):
    """
    User model matching existing MySQL schema
    Table: users
    Columns: id, username, password_hash, role, is_active, created_at, updated_at
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum(
            UserRole.SYSTEM_ADMIN,
            UserRole.NETWORK_ENGINEER,
            UserRole.DATA_SCIENTIST,
            UserRole.NOC_OPERATOR,
            name='user_role'
        ),
        nullable=False,
        default=UserRole.NETWORK_ENGINEER
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def set_password(self, password):
        """
        Hash and set password
        Uses Werkzeug's secure hashing (PBKDF2)
        """
        if len(password) < 12:
            raise ValueError('Password must be at least 12 characters')
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Verify password against hash
        
        Args:
            password (str): Plain text password to verify
            
        Returns:
            bool: True if password matches hash
        """
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, *roles):
        """
        Check if user has one of the specified roles
        
        Args:
            *roles: Role strings to check
            
        Returns:
            bool: True if user has any of the specified roles
        """
        return self.role in roles
    
    def is_admin(self):
        """Check if user is system administrator"""
        return self.role == UserRole.SYSTEM_ADMIN
    
    def is_network_engineer(self):
        """Check if user is network engineer"""
        return self.role == UserRole.NETWORK_ENGINEER
    
    def is_data_scientist(self):
        """Check if user is data scientist"""
        return self.role == UserRole.DATA_SCIENTIST
    
    def is_noc_operator(self):
        """Check if user is NOC operator"""
        return self.role == UserRole.NOC_OPERATOR
    
    def get_role_label(self):
        """Get display label for user's role"""
        return UserRole.get_label(self.role)
    
    def generate_otp(self):
        """
        Generate 6-digit OTP and store with expiry (10 minutes)
        Returns the OTP code
        """
        self.otp_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        self.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()
        return self.otp_code
    
    def verify_otp(self, otp_code):
        """
        Verify OTP code and check expiry
        Returns True if valid, False otherwise
        """
        if not self.otp_code or not self.otp_expiry:
            return False
        
        if datetime.utcnow() > self.otp_expiry:
            return False
        
        return self.otp_code == otp_code
    
    def mark_email_verified(self):
        """Mark email as verified and clear OTP"""
        self.email_verified = True
        self.otp_code = None
        self.otp_expiry = None
        db.session.commit()
    
    def generate_reset_token(self):
        """
        Generate password reset token and store with expiry (1 hour)
        Returns the token
        """
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return self.reset_token
    
    def verify_reset_token(self, token):
        """
        Verify reset token and check expiry
        Returns True if valid, False otherwise
        """
        if not self.reset_token or not self.reset_token_expiry:
            return False
        
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        
        return self.reset_token == token
    
    def clear_reset_token(self):
        """Clear reset token after use"""
        self.reset_token = None
        self.reset_token_expiry = None
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
