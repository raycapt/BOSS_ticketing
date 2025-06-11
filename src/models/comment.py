from datetime import datetime
from src.models.database import db

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert comment object to dictionary"""
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'user_name': self.author.name if self.author else None,
            'user_organization': self.author.organization if self.author else None,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Comment {self.id} on Ticket {self.ticket_id}>'

