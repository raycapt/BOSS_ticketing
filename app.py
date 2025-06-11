from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Simple test route
@app.route('/')
def home():
    return jsonify({
        "message": "BOSS Ticketing API is running!",
        "status": "success",
        "version": "1.0"
    })

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "message": "API is working correctly"
    })

# Test login endpoint
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

