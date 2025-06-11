from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from src.models.database import db
from src.models.comment import Comment
from src.models.ticket import Ticket
from src.utils.auth import get_current_user
from src.utils.validators import validate_required_fields

comments_bp = Blueprint('comments', __name__)

@comments_bp.route('/ticket/<int:ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket_comments(ticket_id):
    """Get all comments for a specific ticket"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if ticket exists
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Check access permissions
        if current_user.organization == 'Oldendorff' and ticket.creator_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get comments ordered by creation date
        comments = Comment.query.filter_by(ticket_id=ticket_id).order_by(Comment.created_at.asc()).all()
        
        return jsonify({
            'comments': [comment.to_dict() for comment in comments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve comments'}), 500

@comments_bp.route('/ticket/<int:ticket_id>', methods=['POST'])
@jwt_required()
def add_comment(ticket_id):
    """Add a comment to a ticket"""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate required fields
        validate_required_fields(data, ['content'])
        
        content = data['content'].strip()
        
        if not content:
            return jsonify({'error': 'Comment content cannot be empty'}), 400
        
        # Check if ticket exists
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Check access permissions
        if current_user.organization == 'Oldendorff' and ticket.creator_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Create new comment
        comment = Comment(
            ticket_id=ticket_id,
            user_id=current_user.id,
            content=content
        )
        
        db.session.add(comment)
        
        # Update ticket's updated_at timestamp
        ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add comment'}), 500

@comments_bp.route('/<int:comment_id>', methods=['GET'])
@jwt_required()
def get_comment(comment_id):
    """Get specific comment by ID"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        comment = Comment.query.get(comment_id)
        
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Check access permissions through ticket
        ticket = comment.ticket
        if current_user.organization == 'Oldendorff' and ticket.creator_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'comment': comment.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve comment'}), 500

@comments_bp.route('/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """Update comment (only by comment author)"""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        comment = Comment.query.get(comment_id)
        
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Only comment author can edit their comment
        if comment.user_id != current_user.id:
            return jsonify({'error': 'You can only edit your own comments'}), 403
        
        # Validate required fields
        validate_required_fields(data, ['content'])
        
        content = data['content'].strip()
        
        if not content:
            return jsonify({'error': 'Comment content cannot be empty'}), 400
        
        # Update comment
        comment.content = content
        
        # Update ticket's updated_at timestamp
        comment.ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Comment updated successfully',
            'comment': comment.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update comment'}), 500

@comments_bp.route('/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Delete comment (only by comment author or admin)"""
    try:
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        comment = Comment.query.get(comment_id)
        
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Only comment author or admin can delete comment
        if comment.user_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'You can only delete your own comments'}), 403
        
        # Update ticket's updated_at timestamp before deleting comment
        comment.ticket.updated_at = datetime.utcnow()
        
        # Delete comment
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Comment deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete comment'}), 500

@comments_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_comments(user_id):
    """Get all comments by a specific user (admin only or own comments)"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Users can only see their own comments, admins can see any user's comments
        if current_user.id != user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get comments with pagination
        comments_query = Comment.query.filter_by(user_id=user_id).order_by(Comment.created_at.desc())
        comments_paginated = comments_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'comments': [comment.to_dict() for comment in comments_paginated.items],
            'total': comments_paginated.total,
            'page': page,
            'pages': comments_paginated.pages,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve user comments'}), 500

@comments_bp.route('/test')
def comments_test():
    """Test endpoint to verify comments blueprint is working"""
    return jsonify({'message': 'Comments blueprint working'}), 200

