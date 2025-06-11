import os
import uuid
import mimetypes
from werkzeug.utils import secure_filename
from flask import current_app
from src.utils.validators import validate_file_size, sanitize_filename

class FileHandler:
    """Handle file upload, storage, and retrieval operations"""
    
    @staticmethod
    def get_upload_path(ticket_id):
        """Get the upload directory path for a specific ticket"""
        upload_folder = current_app.config['UPLOAD_FOLDER']
        ticket_folder = os.path.join(upload_folder, 'tickets', str(ticket_id))
        
        # Create directory if it doesn't exist
        os.makedirs(ticket_folder, exist_ok=True)
        
        return ticket_folder
    
    @staticmethod
    def generate_unique_filename(original_filename):
        """Generate a unique filename while preserving the extension"""
        # Sanitize the original filename
        safe_filename = sanitize_filename(original_filename)
        
        # Split filename and extension
        name, ext = os.path.splitext(safe_filename)
        
        # Generate unique identifier
        unique_id = str(uuid.uuid4())[:8]
        
        # Combine to create unique filename
        unique_filename = f"{name}_{unique_id}{ext}"
        
        return unique_filename
    
    @staticmethod
    def save_file(file, ticket_id):
        """Save uploaded file and return file information"""
        if not file or not file.filename:
            raise ValueError("No file provided")
        
        # Get file information
        original_filename = file.filename
        file_size = 0
        
        # Read file content to get size and validate
        file_content = file.read()
        file_size = len(file_content)
        
        # Reset file pointer
        file.seek(0)
        
        # Validate file size
        validate_file_size(file_size)
        
        # Get MIME type
        mime_type = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
        
        # Generate unique filename
        stored_filename = FileHandler.generate_unique_filename(original_filename)
        
        # Get upload path
        upload_path = FileHandler.get_upload_path(ticket_id)
        file_path = os.path.join(upload_path, stored_filename)
        
        # Save file
        file.save(file_path)
        
        return {
            'original_filename': original_filename,
            'stored_filename': stored_filename,
            'file_path': file_path,
            'file_size': file_size,
            'mime_type': mime_type
        }
    
    @staticmethod
    def delete_file(file_path):
        """Delete a file from storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass
        return False
    
    @staticmethod
    def get_file_info(file_path):
        """Get information about a stored file"""
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        return {
            'exists': True,
            'size': stat.st_size,
            'modified': stat.st_mtime
        }
    
    @staticmethod
    def validate_file_access(file_path, ticket_id):
        """Validate that file belongs to the specified ticket"""
        expected_path = FileHandler.get_upload_path(ticket_id)
        return file_path.startswith(expected_path)
    
    @staticmethod
    def get_allowed_extensions():
        """Get list of allowed file extensions (all formats allowed)"""
        return None  # None means all extensions are allowed
    
    @staticmethod
    def is_allowed_file(filename):
        """Check if file type is allowed (all types allowed in our case)"""
        return True  # All file types are allowed as per requirements

