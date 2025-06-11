from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from src.models.user import User

def admin_required():
    """Decorator to require admin role"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = int(get_jwt_identity())
            user = User.query.get(current_user_id)
            
            if not user or user.role != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def boss_required():
    """Decorator to require BOSS organization"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = int(get_jwt_identity())
            user = User.query.get(current_user_id)
            
            if not user or user.organization != 'BOSS':
                return jsonify({'error': 'BOSS access required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get current user from JWT token"""
    try:
        verify_jwt_in_request()
        current_user_id = int(get_jwt_identity())
        return User.query.get(current_user_id)
    except:
        return None

def validate_email_domain(email):
    """Validate email domain and return organization"""
    if email.endswith('@bwesglobal.com'):
        return 'BOSS'
    elif email.endswith('@oldendorff.com'):
        return 'Oldendorff'
    else:
        raise ValueError("Invalid email domain. Must be @bwesglobal.com or @oldendorff.com")

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one number")
    
    return True

