# Ticketing System - BOSS & Oldendorff

A comprehensive ticketing application for managing service requests between BOSS (service provider) and Oldendorff (client).

## Features

- **User Authentication** - JWT-based with role controls
- **Dashboard Analytics** - Real-time statistics and charts
- **Ticket Management** - Complete CRUD with workflows
- **File Upload System** - 25MB limit, all formats supported
- **Search & Filtering** - Advanced search capabilities
- **Category Management** - Configurable by admins
- **Organization-based Access** - BOSS sees all, Oldendorff sees their own
- **Priority & Status Workflows** - Separate flows for Issues vs Enhancements
- **Comment System** - Full discussion threads on tickets
- **Timeline & Progress Tracking** - Manual updates by BOSS team

## Tech Stack

- **Backend**: Flask, SQLAlchemy, JWT
- **Database**: SQLite (production-ready for PostgreSQL)
- **Authentication**: JWT with role-based access control
- **File Storage**: Local filesystem (cloud-ready)

## Deployment

This application is configured for Railway deployment with:
- `Procfile` for process management
- `requirements.txt` for dependencies
- `runtime.txt` for Python version
- Environment variable support

## Environment Variables

- `FLASK_ENV` - Set to 'production' for deployment
- `JWT_SECRET_KEY` - Secret key for JWT token signing
- `PORT` - Port number (auto-set by Railway)

## Demo Credentials

- **Admin**: admin@bwesglobal.com / admin123

## API Endpoints

- `/api/auth/*` - Authentication endpoints
- `/api/tickets/*` - Ticket management
- `/api/users/*` - User management
- `/api/dashboard/*` - Analytics and reporting
- `/api/categories/*` - Category management
- `/api/files/*` - File upload/download
- `/api/search/*` - Search functionality

## Organization Assignment

Users are automatically assigned to organizations based on email domain:
- `@bwesglobal.com` → BOSS
- `@oldendorff.com` → Oldendorff

## License

Private application for BOSS & Oldendorff.

