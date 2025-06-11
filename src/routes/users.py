from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db
from src.models.user import User
from src.utils.auth import admin_required, get_current_user, validate_email_domain, validate_password
from src.utils.validators import validate_required_fields, validate_email

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
@admin_required()
def get_users():
    """Get all users (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Query users with pagination
        users_query = User.query.order_by(User.created_at.desc())
        users_paginated = users_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users_paginated.items],
            'total': users_paginated.total,
            'page': page,
            'pages': users_paginated.pages,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve users'}), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
@admin_required()
def get_user(user_id):
    """Get specific user by ID (admin only)"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve user'}), 500

@users_bp.route('/<int:user_id>', methods=['PUT'])
@admin_required()
def update_user(user_id):
    """Update user details (admin only)"""
    try:
        data = request.get_json()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name'].strip()
        
        if 'role' in data:
            if data['role'] not in ['admin', 'normal']:
                return jsonify({'error': 'Invalid role. Must be admin or normal'}), 400
            user.role = data['role']
        
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        
        # Email changes require validation
        if 'email' in data:
            new_email = data['email'].lower().strip()
            
            # Validate email format
            validate_email(new_email)
            
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': 'Email already taken by another user'}), 400
            
            # Validate email domain and update organization
            try:
                organization = validate_email_domain(new_email)
                user.email = new_email
                user.organization = organization
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user'}), 500

@users_bp.route('/<int:user_id>/reset-password', methods=['POST'])
@admin_required()
def reset_user_password(user_id):
    """Reset user password (admin only)"""
    try:
        data = request.get_json()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate required fields
        validate_required_fields(data, ['new_password'])
        
        new_password = data['new_password']
        
        # Validate password strength
        validate_password(new_password)
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'message': 'Password reset successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Password reset failed'}), 500

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required()
def delete_user(user_id):
    """Deactivate user (admin only) - we don't actually delete to preserve data integrity"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Don't allow deleting the current admin user
        current_user_id = get_jwt_identity()
        if user.id == current_user_id:
            return jsonify({'error': 'Cannot deactivate your own account'}), 400
        
        # Deactivate instead of delete
        user.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'User deactivated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to deactivate user'}), 500

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user's profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get profile'}), 500

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user's profile (limited fields)"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Users can only update their name
        if 'name' in data:
            user.name = data['name'].strip()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500

@users_bp.route('/test')
def users_test():
    """Test endpoint to verify users blueprint is working"""
    return jsonify({'message': 'Users blueprint working'}), 200

