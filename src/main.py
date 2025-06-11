import os
import sys
from datetime import timedelta
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database and models
from src.models.database import db
from src.models.user import User
from src.models.category import Category
from src.models.ticket import Ticket
from src.models.comment import Comment
from src.models.file import File

# Import blueprints
from src.routes.auth import auth_bp
from src.routes.users import users_bp
from src.routes.categories import categories_bp
from src.routes.tickets import tickets_bp
from src.routes.comments import comments_bp
from src.routes.files import files_bp
from src.routes.dashboard import dashboard_bp
from src.routes.search import search_bp

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Database configuration - using SQLite for development
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ticketing.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # File upload configuration
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB max file size
    
    # Initialize extensions
    CORS(app, origins="*")  # Allow all origins for development
    jwt = JWTManager(app)
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(categories_bp, url_prefix='/api/categories')
    app.register_blueprint(tickets_bp, url_prefix='/api/tickets')
    app.register_blueprint(comments_bp, url_prefix='/api/comments')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    
    # Create database tables and seed initial data
    with app.app_context():
        db.create_all()
        seed_initial_data()
    
    # Serve React frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "index.html not found", 404
    
    return app

def seed_initial_data():
    """Seed the database with initial data if it doesn't exist"""
    # Check if categories already exist
    if Category.query.count() == 0:
        categories = [
            Category(name='SnC/Modelling', description='Ship and Cargo Modelling related tickets'),
            Category(name='Routing/Wx', description='Routing and Weather related tickets'),
            Category(name='Reporting', description='Reporting functionality tickets'),
            Category(name='Dashboard', description='Dashboard and analytics tickets'),
            Category(name='Emissions', description='Emissions tracking and reporting tickets')
        ]
        
        for category in categories:
            db.session.add(category)
    
    # Check if admin user already exists
    if User.query.filter_by(email='admin@bwesglobal.com').first() is None:
        admin_user = User(
            name='Admin User',
            email='admin@bwesglobal.com',
            role='admin',
            organization='BOSS'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
    
    db.session.commit()

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

