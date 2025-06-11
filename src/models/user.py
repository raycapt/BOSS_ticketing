from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from src.models.database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='normal')  # 'admin' or 'normal'
    organization = db.Column(db.String(50), nullable=False)  # 'BOSS' or 'Oldendorff'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    created_tickets = db.relationship('Ticket', backref='creator', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    uploaded_files = db.relationship('File', backref='uploader', lazy=True)
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the user's password"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def assign_organization(email):
        """Assign organization based on email domain"""
        if email.endswith('@bwesglobal.com'):
            return 'BOSS'
        elif email.endswith('@oldendorff.com'):
            return 'Oldendorff'
        else:
            raise ValueError("Invalid email domain. Must be @bwesglobal.com or @oldendorff.com")
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'organization': self.organization,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<User {self.email}>'

