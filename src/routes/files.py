from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.exceptions import RequestEntityTooLarge
import os
from src.models.database import db
from src.models.file import File
from src.models.ticket import Ticket
from src.utils.auth import get_current_user
from src.utils.file_handler import FileHandler

files_bp = Blueprint('files', __name__)

@files_bp.route('/ticket/<int:ticket_id>/upload', methods=['POST'])
@jwt_required()
def upload_file(ticket_id):
    """Upload file to a specific ticket"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if ticket exists
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Check access permissions
        if current_user.organization == 'Oldendorff' and ticket.creator_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type (all types allowed)
        if not FileHandler.is_allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Save file
        try:
            file_info = FileHandler.save_file(file, ticket_id)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Create file record in database
        file_record = File(
            ticket_id=ticket_id,
            original_filename=file_info['original_filename'],
            stored_filename=file_info['stored_filename'],
            file_path=file_info['file_path'],
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            uploaded_by=current_user.id
        )
        
        db.session.add(file_record)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': file_record.to_dict()
        }), 201
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'File size exceeds maximum limit of 25MB'}), 413
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'File upload failed'}), 500

@files_bp.route('/ticket/<int:ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket_files(ticket_id):
    """Get all files for a specific ticket"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if ticket exists
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Check access permissions
        if current_user.organization == 'Oldendorff' and ticket.creator_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get files for the ticket
        files = File.query.filter_by(ticket_id=ticket_id).order_by(File.uploaded_at.desc()).all()
        
        return jsonify({
            'files': [file.to_dict() for file in files]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve files'}), 500

@files_bp.route('/<int:file_id>/download', methods=['GET'])
@jwt_required()
def download_file(file_id):
    """Download a specific file"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get file record
        file_record = File.query.get(file_id)
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check access permissions through ticket
        ticket = file_record.ticket
        if current_user.organization == 'Oldendorff' and ticket.creator_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Validate file path
        if not FileHandler.validate_file_access(file_record.file_path, file_record.ticket_id):
            return jsonify({'error': 'Invalid file access'}), 403
        
        # Check if file exists
        if not os.path.exists(file_record.file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        # Send file
        return send_file(
            file_record.file_path,
            as_attachment=True,
            download_name=file_record.original_filename,
            mimetype=file_record.mime_type
        )
        
    except Exception as e:
        return jsonify({'error': 'File download failed'}), 500

@files_bp.route('/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file_info(file_id):
    """Get information about a specific file"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get file record
        file_record = File.query.get(file_id)
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check access permissions through ticket
        ticket = file_record.ticket
        if current_user.organization == 'Oldendorff' and ticket.creator_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'file': file_record.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve file information'}), 500

@files_bp.route('/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """Delete a file"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get file record
        file_record = File.query.get(file_id)
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check permissions - file uploader or admin can delete
        if file_record.uploaded_by != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'You can only delete files you uploaded'}), 403
        
        # Delete physical file
        FileHandler.delete_file(file_record.file_path)
        
        # Delete database record
        db.session.delete(file_record)
        db.session.commit()
        
        return jsonify({
            'message': 'File deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete file'}), 500

@files_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_files(user_id):
    """Get all files uploaded by a specific user"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Users can only see their own files, admins can see any user's files
        if current_user.id != user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get files with pagination
        files_query = File.query.filter_by(uploaded_by=user_id).order_by(File.uploaded_at.desc())
        files_paginated = files_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'files': [file.to_dict() for file in files_paginated.items],
            'total': files_paginated.total,
            'page': page,
            'pages': files_paginated.pages,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve user files'}), 500

@files_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_file_stats():
    """Get file upload statistics"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Base query based on user permissions
        base_query = File.query
        
        if current_user.organization == 'Oldendorff':
            # Oldendorff users can only see stats for their tickets
            base_query = base_query.join(Ticket).filter(Ticket.creator_id == current_user.id)
        
        # Total files
        total_files = base_query.count()
        
        # Total size
        total_size = db.session.query(db.func.sum(File.file_size)).scalar() or 0
        
        # Files by type (based on MIME type)
        mime_stats = {}
        files = base_query.all()
        for file in files:
            mime_category = file.mime_type.split('/')[0] if file.mime_type else 'unknown'
            mime_stats[mime_category] = mime_stats.get(mime_category, 0) + 1
        
        return jsonify({
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'files_by_type': mime_stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get file statistics'}), 500

@files_bp.route('/test')
def files_test():
    """Test endpoint to verify files blueprint is working"""
    return jsonify({'message': 'Files blueprint working'}), 200

