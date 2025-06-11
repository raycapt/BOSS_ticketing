from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
CORS(app)

# In-memory data storage (for demo purposes)
tickets = []
categories = [
    {"id": 1, "name": "SnC/Modelling", "description": "Ship and Cargo Modelling"},
    {"id": 2, "name": "Routing/Wx", "description": "Routing and Weather"},
    {"id": 3, "name": "Reporting", "description": "Reporting Systems"},
    {"id": 4, "name": "Dashboard", "description": "Dashboard Features"},
    {"id": 5, "name": "Emissions", "description": "Emissions Tracking"}
]

users = [
    {
        "id": 1,
        "name": "Admin User",
        "email": "admin@bwesglobal.com",
        "role": "admin",
        "organization": "BOSS",
        "active": True
    }
]

# Helper functions
def get_organization_from_email(email):
    if "@bwesglobal.com" in email:
        return "BOSS"
    elif "@oldendorff.com" in email:
        return "Oldendorff"
    return "Unknown"

def validate_priority_for_type(priority, ticket_type):
    if ticket_type == "Enhancement" and priority == "Top Urgent":
        return False
    return True

# Simple test route
@app.route('/')
def home():
    return jsonify({
        "message": "BOSS Ticketing API is running!",
        "status": "success",
        "version": "2.0",
        "features": ["Authentication", "Tickets", "Categories", "Users"]
    })

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "message": "API is working correctly",
        "tickets_count": len(tickets),
        "categories_count": len(categories)
    })

# Authentication endpoints
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Simple test login
    if data.get('email') == 'admin@bwesglobal.com' and data.get('password') == 'admin123':
        return jsonify({
            "success": True,
            "token": "test-jwt-token",
            "user": {
                "id": 1,
                "name": "Admin User",
                "email": "admin@bwesglobal.com",
                "role": "admin",
                "organization": "BOSS"
            }
        })
    else:
        return jsonify({
            "success": False,
            "message": "Invalid credentials"
        }), 401

# Categories endpoints
@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify({
        "success": True,
        "categories": categories
    })

@app.route('/api/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    
    new_category = {
        "id": len(categories) + 1,
        "name": data.get('name'),
        "description": data.get('description', '')
    }
    
    categories.append(new_category)
    
    return jsonify({
        "success": True,
        "category": new_category
    }), 201

# Tickets endpoints
@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    # Get query parameters for filtering
    status = request.args.get('status')
    priority = request.args.get('priority')
    category_id = request.args.get('category_id')
    ticket_type = request.args.get('type')
    search = request.args.get('search')
    
    filtered_tickets = tickets.copy()
    
    # Apply filters
    if status:
        filtered_tickets = [t for t in filtered_tickets if t['status'] == status]
    if priority:
        filtered_tickets = [t for t in filtered_tickets if t['priority'] == priority]
    if category_id:
        filtered_tickets = [t for t in filtered_tickets if t['category_id'] == int(category_id)]
    if ticket_type:
        filtered_tickets = [t for t in filtered_tickets if t['type'] == ticket_type]
    if search:
        search_lower = search.lower()
        filtered_tickets = [t for t in filtered_tickets 
                          if search_lower in t['title'].lower() or 
                             search_lower in t['description'].lower()]
    
    return jsonify({
        "success": True,
        "tickets": filtered_tickets,
        "total": len(filtered_tickets)
    })

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'description', 'category_id', 'priority', 'type', 'created_by_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "success": False,
                "message": f"Missing required field: {field}"
            }), 400
    
    # Validate priority for ticket type
    if not validate_priority_for_type(data['priority'], data['type']):
        return jsonify({
            "success": False,
            "message": "Top Urgent priority is only allowed for Issue tickets"
        }), 400
    
    # Create new ticket
    new_ticket = {
        "id": len(tickets) + 1,
        "title": data['title'],
        "description": data['description'],
        "category_id": int(data['category_id']),
        "priority": data['priority'],
        "type": data['type'],
        "status": "In Progress",
        "created_by_name": data['created_by_name'],
        "created_by_email": data.get('created_by_email', 'admin@bwesglobal.com'),
        "organization": get_organization_from_email(data.get('created_by_email', 'admin@bwesglobal.com')),
        "timeline": data.get('timeline'),
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    tickets.append(new_ticket)
    
    return jsonify({
        "success": True,
        "ticket": new_ticket
    }), 201

@app.route('/api/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    ticket = next((t for t in tickets if t['id'] == ticket_id), None)
    
    if not ticket:
        return jsonify({
            "success": False,
            "message": "Ticket not found"
        }), 404
    
    return jsonify({
        "success": True,
        "ticket": ticket
    })

@app.route('/api/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    ticket = next((t for t in tickets if t['id'] == ticket_id), None)
    
    if not ticket:
        return jsonify({
            "success": False,
            "message": "Ticket not found"
        }), 404
    
    data = request.get_json()
    
    # Update allowed fields
    updatable_fields = ['title', 'description', 'category_id', 'priority', 'status', 'timeline', 'progress']
    for field in updatable_fields:
        if field in data:
            if field == 'priority' and data.get('type', ticket['type']):
                if not validate_priority_for_type(data[field], data.get('type', ticket['type'])):
                    return jsonify({
                        "success": False,
                        "message": "Top Urgent priority is only allowed for Issue tickets"
                    }), 400
            ticket[field] = data[field]
    
    ticket['updated_at'] = datetime.now().isoformat()
    
    return jsonify({
        "success": True,
        "ticket": ticket
    })

@app.route('/api/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    global tickets
    ticket = next((t for t in tickets if t['id'] == ticket_id), None)
    
    if not ticket:
        return jsonify({
            "success": False,
            "message": "Ticket not found"
        }), 404
    
    tickets = [t for t in tickets if t['id'] != ticket_id]
    
    return jsonify({
        "success": True,
        "message": "Ticket deleted successfully"
    })

# Dashboard statistics
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    total_tickets = len(tickets)
    completed_tickets = len([t for t in tickets if t['status'] == 'Completed'])
    in_progress_tickets = len([t for t in tickets if t['status'] == 'In Progress'])
    
    # Calculate average resolution time (mock data for now)
    avg_resolution_days = 3 if completed_tickets > 0 else 0
    
    return jsonify({
        "success": True,
        "stats": {
            "total_tickets": total_tickets,
            "completed_tickets": completed_tickets,
            "in_progress_tickets": in_progress_tickets,
            "avg_resolution_time": f"{avg_resolution_days}d"
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

