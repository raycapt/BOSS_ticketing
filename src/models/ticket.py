from datetime import datetime
from src.models.database import db

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    ticket_type = db.Column(db.String(20), nullable=False)  # 'Enhancement' or 'Issue'
    priority = db.Column(db.String(20), nullable=False)  # 'Top Urgent', 'High', 'Medium', 'Low'
    status = db.Column(db.String(20), nullable=False, default='In Progress')
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timeline_date = db.Column(db.Date)
    progress = db.Column(db.Integer, default=0)  # 0-100 in steps of 10
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('Comment', backref='ticket', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('File', backref='ticket', lazy=True, cascade='all, delete-orphan')
    
    @staticmethod
    def validate_priority(ticket_type, priority):
        """Validate priority based on ticket type"""
        if ticket_type == 'Enhancement' and priority == 'Top Urgent':
            raise ValueError("Enhancement tickets cannot have 'Top Urgent' priority")
        
        valid_priorities = {
            'Issue': ['Top Urgent', 'High', 'Medium', 'Low'],
            'Enhancement': ['High', 'Medium', 'Low']
        }
        
        if priority not in valid_priorities.get(ticket_type, []):
            raise ValueError(f"Invalid priority '{priority}' for ticket type '{ticket_type}'")
    
    @staticmethod
    def validate_status_transition(current_status, new_status):
        """Validate status transition"""
        valid_transitions = {
            'In Progress': ['Under Review'],
            'Under Review': ['In Progress', 'Completed'],
            'Completed': ['Closed'],
            'Closed': []  # No transitions from closed
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise ValueError(f"Invalid status transition from '{current_status}' to '{new_status}'")
    
    @staticmethod
    def validate_progress(progress):
        """Validate progress value"""
        if progress < 0 or progress > 100:
            raise ValueError("Progress must be between 0 and 100")
        
        if progress % 10 != 0:
            raise ValueError("Progress must be in steps of 10")
    
    def to_dict(self):
        """Convert ticket object to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'ticket_type': self.ticket_type,
            'priority': self.priority,
            'status': self.status,
            'creator_id': self.creator_id,
            'creator_name': self.creator.name if self.creator else None,
            'creator_organization': self.creator.organization if self.creator else None,
            'timeline_date': self.timeline_date.isoformat() if self.timeline_date else None,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'comments_count': len(self.comments),
            'files_count': len(self.files)
        }
    
    def __repr__(self):
        return f'<Ticket {self.id}: {self.title}>'

