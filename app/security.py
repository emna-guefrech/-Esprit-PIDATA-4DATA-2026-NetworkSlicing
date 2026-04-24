"""
Security and RBAC decorators
Role-based access control decorators for Flask routes
"""
from functools import wraps
from flask import abort, current_app
from flask_login import current_user


def role_required(*allowed_roles):
    """
    Decorator to restrict route access by user role
    
    Usage:
        @role_required('system_admin')
        def admin_route():
            pass
        
        @role_required('network_engineer', 'data_scientist')
        def multi_role_route():
            pass
    
    Args:
        *allowed_roles: Variable number of role strings
    
    Returns:
        Decorated function that checks user role before allowing access
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized
            
            if current_user.role not in allowed_roles:
                abort(403)  # Forbidden
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to restrict route to system_admin role only
    Shorthand for @role_required('system_admin')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        
        if not current_user.is_admin():
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function
