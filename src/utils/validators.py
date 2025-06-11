from flask import request, jsonify
import re

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return True

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    return True

def validate_ticket_type(ticket_type):
    """Validate ticket type"""
    valid_types = ['Enhancement', 'Issue']
    if ticket_type not in valid_types:
        raise ValueError(f"Invalid ticket type. Must be one of: {', '.join(valid_types)}")
    return True

def validate_priority(priority, ticket_type=None):
    """Validate priority based on ticket type"""
    valid_priorities = ['Top Urgent', 'High', 'Medium', 'Low']
    
    if priority not in valid_priorities:
        raise ValueError(f"Invalid priority. Must be one of: {', '.join(valid_priorities)}")
    
    # Top Urgent only for Issues
    if priority == 'Top Urgent' and ticket_type == 'Enhancement':
        raise ValueError("Enhancement tickets cannot have 'Top Urgent' priority")
    
    return True

def validate_status(status):
    """Validate ticket status"""
    valid_statuses = ['In Progress', 'Under Review', 'Completed', 'Closed']
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    return True

def validate_progress(progress):
    """Validate progress value"""
    if not isinstance(progress, int):
        raise ValueError("Progress must be an integer")
    
    if progress < 0 or progress > 100:
        raise ValueError("Progress must be between 0 and 100")
    
    if progress % 10 != 0:
        raise ValueError("Progress must be in steps of 10")
    
    return True

def validate_file_size(file_size, max_size=25*1024*1024):
    """Validate file size (default 25MB)"""
    if file_size > max_size:
        raise ValueError(f"File size exceeds maximum limit of {max_size // (1024*1024)}MB")
    return True

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    # Remove any path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename

