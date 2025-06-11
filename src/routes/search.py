from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.database import db
from src.models.ticket import Ticket
from src.models.category import Category
from src.models.user import User
from src.utils.auth import get_current_user

search_bp = Blueprint('search', __name__)

@search_bp.route('/tickets', methods=['GET'])
@jwt_required()
def search_tickets():
    """Search tickets by keywords in title and description"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get search parameters
        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Base query based on user organization
        base_query = Ticket.query
        if current_user.organization == 'Oldendorff':
            base_query = base_query.filter(Ticket.creator_id == current_user.id)
        
        # Search in title and description
        search_term = f"%{query}%"
        search_query = base_query.filter(
            db.or_(
                Ticket.title.ilike(search_term),
                Ticket.description.ilike(search_term)
            )
        ).order_by(Ticket.created_at.desc())
        
        # Paginate results
        tickets_paginated = search_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'tickets': [ticket.to_dict() for ticket in tickets_paginated.items],
            'total': tickets_paginated.total,
            'page': page,
            'pages': tickets_paginated.pages,
            'per_page': per_page,
            'query': query
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Search failed'}), 500

@search_bp.route('/tickets/advanced', methods=['GET'])
@jwt_required()
def advanced_search_tickets():
    """Advanced search with multiple filters"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get search parameters
        query = request.args.get('q', '').strip()
        status = request.args.get('status')
        category_id = request.args.get('category', type=int)
        priority = request.args.get('priority')
        ticket_type = request.args.get('type')
        creator_id = request.args.get('creator', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Base query based on user organization
        base_query = Ticket.query
        if current_user.organization == 'Oldendorff':
            base_query = base_query.filter(Ticket.creator_id == current_user.id)
        
        # Apply text search if provided
        if query:
            search_term = f"%{query}%"
            base_query = base_query.filter(
                db.or_(
                    Ticket.title.ilike(search_term),
                    Ticket.description.ilike(search_term)
                )
            )
        
        # Apply filters
        if status:
            base_query = base_query.filter(Ticket.status == status)
        
        if category_id:
            base_query = base_query.filter(Ticket.category_id == category_id)
        
        if priority:
            base_query = base_query.filter(Ticket.priority == priority)
        
        if ticket_type:
            base_query = base_query.filter(Ticket.ticket_type == ticket_type)
        
        if creator_id and current_user.organization == 'BOSS':
            # Only BOSS users can filter by creator
            base_query = base_query.filter(Ticket.creator_id == creator_id)
        
        # Date range filters
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                base_query = base_query.filter(Ticket.created_at >= date_from_obj)
            except ValueError:
                return jsonify({'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
        
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                # Add one day to include the entire day
                date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
                base_query = base_query.filter(Ticket.created_at <= date_to_obj)
            except ValueError:
                return jsonify({'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
        
        # Order by relevance (if text search) or creation date
        if query:
            # For text search, order by creation date (could be enhanced with relevance scoring)
            base_query = base_query.order_by(Ticket.created_at.desc())
        else:
            base_query = base_query.order_by(Ticket.created_at.desc())
        
        # Paginate results
        tickets_paginated = base_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'tickets': [ticket.to_dict() for ticket in tickets_paginated.items],
            'total': tickets_paginated.total,
            'page': page,
            'pages': tickets_paginated.pages,
            'per_page': per_page,
            'filters': {
                'query': query,
                'status': status,
                'category_id': category_id,
                'priority': priority,
                'ticket_type': ticket_type,
                'creator_id': creator_id,
                'date_from': date_from,
                'date_to': date_to
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Advanced search failed'}), 500

@search_bp.route('/suggestions', methods=['GET'])
@jwt_required()
def get_search_suggestions():
    """Get search suggestions based on existing ticket titles"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 5, type=int)
        
        if not query or len(query) < 2:
            return jsonify({'suggestions': []}), 200
        
        # Base query based on user organization
        base_query = Ticket.query
        if current_user.organization == 'Oldendorff':
            base_query = base_query.filter(Ticket.creator_id == current_user.id)
        
        # Search for similar titles
        search_term = f"%{query}%"
        suggestions_query = base_query.filter(
            Ticket.title.ilike(search_term)
        ).order_by(Ticket.created_at.desc()).limit(limit)
        
        suggestions = []
        for ticket in suggestions_query:
            suggestions.append({
                'text': ticket.title,
                'ticket_id': ticket.id,
                'category': ticket.category.name if ticket.category else None
            })
        
        return jsonify({
            'suggestions': suggestions
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get suggestions'}), 500

@search_bp.route('/filters', methods=['GET'])
@jwt_required()
def get_search_filters():
    """Get available filter options for advanced search"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get available categories
        categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
        category_options = [{'id': cat.id, 'name': cat.name} for cat in categories]
        
        # Get available statuses
        status_options = ['In Progress', 'Under Review', 'Completed', 'Closed']
        
        # Get available priorities
        priority_options = ['Top Urgent', 'High', 'Medium', 'Low']
        
        # Get available ticket types
        type_options = ['Enhancement', 'Issue']
        
        # Get available creators (only for BOSS users)
        creator_options = []
        if current_user.organization == 'BOSS':
            creators = User.query.filter_by(is_active=True).order_by(User.name).all()
            creator_options = [{'id': user.id, 'name': user.name, 'organization': user.organization} for user in creators]
        
        return jsonify({
            'categories': category_options,
            'statuses': status_options,
            'priorities': priority_options,
            'types': type_options,
            'creators': creator_options
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get filter options'}), 500

@search_bp.route('/test')
def search_test():
    """Test endpoint to verify search blueprint is working"""
    return jsonify({'message': 'Search blueprint working'}), 200

