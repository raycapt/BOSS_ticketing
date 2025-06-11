from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from src.models.database import db
from src.models.ticket import Ticket
from src.models.category import Category
from src.models.user import User
from src.utils.auth import admin_required, boss_required, get_current_user
from src.utils.validators import validate_required_fields, validate_ticket_type, validate_priority, validate_status, validate_progress

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/', methods=['GET'])
@jwt_required()
def get_tickets():
    """Get tickets with filtering and pagination"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filter parameters
        status = request.args.get('status')
        category_id = request.args.get('category', type=int)
        priority = request.args.get('priority')
        ticket_type = request.args.get('type')
        search = request.args.get('search')
        
        # Base query
        query = Ticket.query
        
        # Organization-based filtering
        if current_user.organization == 'Oldendorff':
            # Oldendorff users can only see their own tickets
            query = query.filter(Ticket.creator_id == current_user.id)
        # BOSS users can see all tickets
        
        # Apply filters
        if status:
            query = query.filter(Ticket.status == status)
        
        if category_id:
            query = query.filter(Ticket.category_id == category_id)
        
        if priority:
            query = query.filter(Ticket.priority == priority)
        
        if ticket_type:
            query = query.filter(Ticket.ticket_type == ticket_type)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Ticket.title.ilike(search_term),
                    Ticket.description.ilike(search_term)
                )
            )
        
        # Order by creation date (newest first)
        query = query.order_by(Ticket.created_at.desc())
        
        # Paginate results
        tickets_paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'tickets': [ticket.to_dict() for ticket in tickets_paginated.items],
            'total': tickets_paginated.total,
            'page': page,
            'pages': tickets_paginated.pages,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve tickets'}), 500

@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket(ticket_id):
    """Get specific ticket by ID"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        ticket = Ticket.query.get(ticket_id)
        
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Check access permissions
        if current_user.organization == 'Oldendorff' and ticket.creator_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get ticket details with related data
        ticket_data = ticket.to_dict()
        
        # Add comments
        comments = [comment.to_dict() for comment in ticket.comments]
        ticket_data['comments'] = comments
        
        # Add files
        files = [file.to_dict() for file in ticket.files]
        ticket_data['files'] = files
        
        return jsonify({
            'ticket': ticket_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve ticket'}), 500

@tickets_bp.route('/', methods=['POST'])
@jwt_required()
def create_ticket():
    """Create a new ticket"""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate required fields
        validate_required_fields(data, ['title', 'description', 'category_id', 'ticket_type', 'priority'])
        
        title = data['title'].strip()
        description = data['description'].strip()
        category_id = data['category_id']
        ticket_type = data['ticket_type']
        priority = data['priority']
        
        # Validate ticket type
        validate_ticket_type(ticket_type)
        
        # Validate priority for ticket type
        validate_priority(priority, ticket_type)
        
        # Validate category exists
        category = Category.query.get(category_id)
        if not category or not category.is_active:
            return jsonify({'error': 'Invalid or inactive category'}), 400
        
        # Create new ticket
        ticket = Ticket(
            title=title,
            description=description,
            category_id=category_id,
            ticket_type=ticket_type,
            priority=priority,
            creator_id=current_user.id,
            status='In Progress'  # Default status
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        return jsonify({
            'message': 'Ticket created successfully',
            'ticket': ticket.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create ticket'}), 500

@tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
@jwt_required()
def update_ticket(ticket_id):
    """Update ticket details"""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        ticket = Ticket.query.get(ticket_id)
        
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Check permissions
        can_edit_basic = (ticket.creator_id == current_user.id)  # Creator can edit basic fields
        can_edit_status = (current_user.organization == 'BOSS')  # Only BOSS can edit status/progress/timeline
        
        if not can_edit_basic and not can_edit_status:
            return jsonify({'error': 'Access denied'}), 403
        
        # Update basic fields (creator or BOSS can edit)
        if can_edit_basic or can_edit_status:
            if 'title' in data:
                ticket.title = data['title'].strip()
            
            if 'description' in data:
                ticket.description = data['description'].strip()
            
            if 'category_id' in data:
                category = Category.query.get(data['category_id'])
                if not category or not category.is_active:
                    return jsonify({'error': 'Invalid or inactive category'}), 400
                ticket.category_id = data['category_id']
            
            if 'ticket_type' in data:
                validate_ticket_type(data['ticket_type'])
                # If changing type, validate priority is still valid
                new_priority = data.get('priority', ticket.priority)
                validate_priority(new_priority, data['ticket_type'])
                ticket.ticket_type = data['ticket_type']
            
            if 'priority' in data:
                validate_priority(data['priority'], ticket.ticket_type)
                ticket.priority = data['priority']
        
        # Update status/progress/timeline (only BOSS can edit)
        if can_edit_status:
            if 'status' in data:
                new_status = data['status']
                validate_status(new_status)
                
                # Validate status transition
                try:
                    Ticket.validate_status_transition(ticket.status, new_status)
                    ticket.status = new_status
                except ValueError as e:
                    return jsonify({'error': str(e)}), 400
            
            if 'progress' in data:
                progress = data['progress']
                validate_progress(progress)
                ticket.progress = progress
            
            if 'timeline_date' in data:
                if data['timeline_date']:
                    try:
                        timeline_date = datetime.strptime(data['timeline_date'], '%Y-%m-%d').date()
                        ticket.timeline_date = timeline_date
                    except ValueError:
                        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
                else:
                    ticket.timeline_date = None
        
        # Update timestamp
        ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Ticket updated successfully',
            'ticket': ticket.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update ticket'}), 500

@tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
@admin_required()
def delete_ticket(ticket_id):
    """Delete ticket (admin only)"""
    try:
        ticket = Ticket.query.get(ticket_id)
        
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Delete ticket (cascade will handle comments and files)
        db.session.delete(ticket)
        db.session.commit()
        
        return jsonify({
            'message': 'Ticket deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete ticket'}), 500

@tickets_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_ticket_stats():
    """Get ticket statistics for current user's view"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Base query based on user organization
        base_query = Ticket.query
        if current_user.organization == 'Oldendorff':
            base_query = base_query.filter(Ticket.creator_id == current_user.id)
        
        # Total tickets
        total_tickets = base_query.count()
        
        # Tickets by status
        status_counts = {}
        for status in ['In Progress', 'Under Review', 'Completed', 'Closed']:
            count = base_query.filter(Ticket.status == status).count()
            status_counts[status] = count
        
        # Tickets by priority
        priority_counts = {}
        for priority in ['Top Urgent', 'High', 'Medium', 'Low']:
            count = base_query.filter(Ticket.priority == priority).count()
            priority_counts[priority] = count
        
        # Tickets by type
        type_counts = {}
        for ticket_type in ['Enhancement', 'Issue']:
            count = base_query.filter(Ticket.ticket_type == ticket_type).count()
            type_counts[ticket_type] = count
        
        return jsonify({
            'total_tickets': total_tickets,
            'by_status': status_counts,
            'by_priority': priority_counts,
            'by_type': type_counts
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get ticket statistics'}), 500

@tickets_bp.route('/test')
def tickets_test():
    """Test endpoint to verify tickets blueprint is working"""
    return jsonify({'message': 'Tickets blueprint working'}), 200

