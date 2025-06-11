from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.database import db
from src.models.user import User
from src.utils.auth import admin_required, get_current_user, validate_email_domain, validate_password
from src.utils.validators import validate_required_fields, validate_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        validate_required_fields(data, ['email', 'password'])
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'token': access_token,
            'user': user.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/register', methods=['POST'])
@admin_required()
def register():
    """Admin-only user registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        validate_required_fields(data, ['name', 'email', 'password'])
        
        name = data['name'].strip()
        email = data['email'].lower().strip()
        password = data['password']
        role = data.get('role', 'normal')
        
        # Validate email format
        validate_email(email)
        
        # Validate password strength
        validate_password(password)
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Determine organization from email domain
        try:
            organization = validate_email_domain(email)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Validate role
        if role not in ['admin', 'normal']:
            return jsonify({'error': 'Invalid role. Must be admin or normal'}), 400
        
        # Create new user
        user = User(
            name=name,
            email=email,
            role=role,
            organization=organization
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'User registration failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """Get current user information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get user information'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        # Validate required fields
        validate_required_fields(data, ['current_password', 'new_password'])
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Get current user
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        validate_password(new_password)
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Password change failed'}), 500

@auth_bp.route('/test')
def auth_test():
    """Test endpoint to verify auth blueprint is working"""
    return jsonify({'message': 'Auth blueprint working'}), 200

