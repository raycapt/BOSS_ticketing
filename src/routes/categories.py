from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db
from src.models.category import Category
from src.utils.auth import admin_required, get_current_user
from src.utils.validators import validate_required_fields

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/', methods=['GET'])
@jwt_required()
def get_categories():
    """Get all active categories"""
    try:
        # Get only active categories
        categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
        
        return jsonify({
            'categories': [category.to_dict() for category in categories]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve categories'}), 500

@categories_bp.route('/all', methods=['GET'])
@admin_required()
def get_all_categories():
    """Get all categories including inactive ones (admin only)"""
    try:
        categories = Category.query.order_by(Category.name).all()
        
        return jsonify({
            'categories': [category.to_dict() for category in categories]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve categories'}), 500

@categories_bp.route('/<int:category_id>', methods=['GET'])
@jwt_required()
def get_category(category_id):
    """Get specific category by ID"""
    try:
        category = Category.query.get(category_id)
        
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        return jsonify({
            'category': category.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve category'}), 500

@categories_bp.route('/', methods=['POST'])
@admin_required()
def create_category():
    """Create a new category (admin only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        validate_required_fields(data, ['name'])
        
        name = data['name'].strip()
        description = data.get('description', '').strip()
        
        # Check if category with same name already exists
        existing_category = Category.query.filter_by(name=name).first()
        if existing_category:
            return jsonify({'error': 'Category with this name already exists'}), 400
        
        # Create new category
        category = Category(
            name=name,
            description=description if description else None
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'message': 'Category created successfully',
            'category': category.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create category'}), 500

@categories_bp.route('/<int:category_id>', methods=['PUT'])
@admin_required()
def update_category(category_id):
    """Update category details (admin only)"""
    try:
        data = request.get_json()
        category = Category.query.get(category_id)
        
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        # Update name if provided
        if 'name' in data:
            new_name = data['name'].strip()
            
            # Check if another category with same name exists
            existing_category = Category.query.filter_by(name=new_name).first()
            if existing_category and existing_category.id != category.id:
                return jsonify({'error': 'Category with this name already exists'}), 400
            
            category.name = new_name
        
        # Update description if provided
        if 'description' in data:
            description = data['description'].strip()
            category.description = description if description else None
        
        # Update active status if provided
        if 'is_active' in data:
            category.is_active = bool(data['is_active'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Category updated successfully',
            'category': category.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update category'}), 500

@categories_bp.route('/<int:category_id>/deactivate', methods=['POST'])
@admin_required()
def deactivate_category(category_id):
    """Deactivate category (admin only) - we don't delete to preserve data integrity"""
    try:
        category = Category.query.get(category_id)
        
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        # Check if category has active tickets
        active_tickets_count = len([t for t in category.tickets if t.status != 'Closed'])
        
        if active_tickets_count > 0:
            return jsonify({
                'error': f'Cannot deactivate category with {active_tickets_count} active tickets'
            }), 400
        
        # Deactivate category
        category.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Category deactivated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to deactivate category'}), 500

@categories_bp.route('/<int:category_id>/activate', methods=['POST'])
@admin_required()
def activate_category(category_id):
    """Activate category (admin only)"""
    try:
        category = Category.query.get(category_id)
        
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        # Activate category
        category.is_active = True
        db.session.commit()
        
        return jsonify({
            'message': 'Category activated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to activate category'}), 500

@categories_bp.route('/test')
def categories_test():
    """Test endpoint to verify categories blueprint is working"""
    return jsonify({'message': 'Categories blueprint working'}), 200

