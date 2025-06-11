from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from src.models.database import db
from src.models.ticket import Ticket
from src.models.category import Category
from src.models.user import User
from src.models.comment import Comment
from src.models.file import File
from src.utils.auth import get_current_user

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
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
        status_stats = {}
        for status in ['In Progress', 'Under Review', 'Completed', 'Closed']:
            count = base_query.filter(Ticket.status == status).count()
            status_stats[status] = count
        
        # Tickets by category
        category_stats = {}
        categories = Category.query.filter_by(is_active=True).all()
        for category in categories:
            count = base_query.filter(Ticket.category_id == category.id).count()
            if count > 0:  # Only include categories with tickets
                category_stats[category.name] = count
        
        # Tickets by priority
        priority_stats = {}
        for priority in ['Top Urgent', 'High', 'Medium', 'Low']:
            count = base_query.filter(Ticket.priority == priority).count()
            priority_stats[priority] = count
        
        # Tickets by type
        type_stats = {}
        for ticket_type in ['Enhancement', 'Issue']:
            count = base_query.filter(Ticket.ticket_type == ticket_type).count()
            type_stats[ticket_type] = count
        
        # Calculate average resolution time
        avg_resolution_time = calculate_average_resolution_time(base_query)
        
        # Recent tickets (last 10)
        recent_tickets = base_query.order_by(Ticket.created_at.desc()).limit(10).all()
        recent_tickets_data = [ticket.to_dict() for ticket in recent_tickets]
        
        # Tickets created this month
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        tickets_this_month = base_query.filter(Ticket.created_at >= current_month_start).count()
        
        # Tickets completed this month
        completed_this_month = base_query.filter(
            Ticket.status == 'Completed',
            Ticket.updated_at >= current_month_start
        ).count()
        
        return jsonify({
            'total_tickets': total_tickets,
            'tickets_by_status': status_stats,
            'tickets_by_category': category_stats,
            'tickets_by_priority': priority_stats,
            'tickets_by_type': type_stats,
            'average_resolution_time_days': avg_resolution_time,
            'recent_tickets': recent_tickets_data,
            'tickets_this_month': tickets_this_month,
            'completed_this_month': completed_this_month
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get dashboard statistics'}), 500

@dashboard_bp.route('/charts', methods=['GET'])
@jwt_required()
def get_chart_data():
    """Get data formatted for charts and visualizations"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Base query based on user organization
        base_query = Ticket.query
        if current_user.organization == 'Oldendorff':
            base_query = base_query.filter(Ticket.creator_id == current_user.id)
        
        # Status chart data
        status_chart = []
        for status in ['In Progress', 'Under Review', 'Completed', 'Closed']:
            count = base_query.filter(Ticket.status == status).count()
            status_chart.append({'name': status, 'value': count})
        
        # Category chart data
        category_chart = []
        categories = Category.query.filter_by(is_active=True).all()
        for category in categories:
            count = base_query.filter(Ticket.category_id == category.id).count()
            if count > 0:
                category_chart.append({'name': category.name, 'value': count})
        
        # Priority chart data
        priority_chart = []
        for priority in ['Top Urgent', 'High', 'Medium', 'Low']:
            count = base_query.filter(Ticket.priority == priority).count()
            if count > 0:
                priority_chart.append({'name': priority, 'value': count})
        
        # Monthly trends (last 6 months)
        monthly_trends = get_monthly_trends(base_query)
        
        # Progress distribution
        progress_distribution = get_progress_distribution(base_query)
        
        return jsonify({
            'status_chart': status_chart,
            'category_chart': category_chart,
            'priority_chart': priority_chart,
            'monthly_trends': monthly_trends,
            'progress_distribution': progress_distribution
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get chart data'}), 500

@dashboard_bp.route('/activity', methods=['GET'])
@jwt_required()
def get_activity_feed():
    """Get recent activity feed"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get recent tickets, comments, and files
        activities = []
        
        # Recent tickets
        base_query = Ticket.query
        if current_user.organization == 'Oldendorff':
            base_query = base_query.filter(Ticket.creator_id == current_user.id)
        
        recent_tickets = base_query.order_by(Ticket.created_at.desc()).limit(5).all()
        for ticket in recent_tickets:
            activities.append({
                'type': 'ticket_created',
                'timestamp': ticket.created_at.isoformat(),
                'description': f'Ticket "{ticket.title}" was created',
                'ticket_id': ticket.id,
                'user_name': ticket.creator.name
            })
        
        # Recent comments (if user can access the tickets)
        comment_query = Comment.query.join(Ticket)
        if current_user.organization == 'Oldendorff':
            comment_query = comment_query.filter(Ticket.creator_id == current_user.id)
        
        recent_comments = comment_query.order_by(Comment.created_at.desc()).limit(5).all()
        for comment in recent_comments:
            activities.append({
                'type': 'comment_added',
                'timestamp': comment.created_at.isoformat(),
                'description': f'Comment added to ticket "{comment.ticket.title}"',
                'ticket_id': comment.ticket_id,
                'user_name': comment.author.name
            })
        
        # Sort all activities by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'activities': activities[:10]  # Return top 10 most recent
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get activity feed'}), 500

@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    """Get summary statistics for quick overview"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Base query based on user organization
        base_query = Ticket.query
        if current_user.organization == 'Oldendorff':
            base_query = base_query.filter(Ticket.creator_id == current_user.id)
        
        # Key metrics
        total_tickets = base_query.count()
        open_tickets = base_query.filter(Ticket.status.in_(['In Progress', 'Under Review'])).count()
        completed_tickets = base_query.filter(Ticket.status == 'Completed').count()
        high_priority_tickets = base_query.filter(Ticket.priority.in_(['Top Urgent', 'High'])).count()
        
        # Calculate completion rate
        completion_rate = (completed_tickets / total_tickets * 100) if total_tickets > 0 else 0
        
        # Get overdue tickets (tickets with timeline_date in the past and not completed)
        today = datetime.now().date()
        overdue_tickets = base_query.filter(
            Ticket.timeline_date < today,
            Ticket.status.in_(['In Progress', 'Under Review'])
        ).count()
        
        return jsonify({
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'completed_tickets': completed_tickets,
            'high_priority_tickets': high_priority_tickets,
            'completion_rate': round(completion_rate, 1),
            'overdue_tickets': overdue_tickets
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get summary'}), 500

def calculate_average_resolution_time(base_query):
    """Calculate average resolution time in days"""
    try:
        completed_tickets = base_query.filter(Ticket.status == 'Completed').all()
        
        if not completed_tickets:
            return 0
        
        total_days = 0
        count = 0
        
        for ticket in completed_tickets:
            if ticket.created_at and ticket.updated_at:
                resolution_time = ticket.updated_at - ticket.created_at
                total_days += resolution_time.days
                count += 1
        
        return round(total_days / count, 1) if count > 0 else 0
        
    except Exception:
        return 0

def get_monthly_trends(base_query):
    """Get monthly ticket creation and completion trends"""
    try:
        trends = []
        
        # Get data for last 6 months
        for i in range(6):
            # Calculate month start and end
            current_date = datetime.now()
            month_start = (current_date.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
            
            # Count tickets created in this month
            created_count = base_query.filter(
                Ticket.created_at >= month_start,
                Ticket.created_at < next_month
            ).count()
            
            # Count tickets completed in this month
            completed_count = base_query.filter(
                Ticket.status == 'Completed',
                Ticket.updated_at >= month_start,
                Ticket.updated_at < next_month
            ).count()
            
            trends.append({
                'month': month_start.strftime('%Y-%m'),
                'created': created_count,
                'completed': completed_count
            })
        
        return list(reversed(trends))  # Reverse to show oldest to newest
        
    except Exception:
        return []

def get_progress_distribution(base_query):
    """Get distribution of ticket progress"""
    try:
        distribution = {}
        
        # Group tickets by progress ranges
        progress_ranges = [
            (0, 0, '0%'),
            (1, 25, '1-25%'),
            (26, 50, '26-50%'),
            (51, 75, '51-75%'),
            (76, 99, '76-99%'),
            (100, 100, '100%')
        ]
        
        for min_progress, max_progress, label in progress_ranges:
            count = base_query.filter(
                Ticket.progress >= min_progress,
                Ticket.progress <= max_progress
            ).count()
            distribution[label] = count
        
        return distribution
        
    except Exception:
        return {}

@dashboard_bp.route('/test')
def dashboard_test():
    """Test endpoint to verify dashboard blueprint is working"""
    return jsonify({'message': 'Dashboard blueprint working'}), 200

