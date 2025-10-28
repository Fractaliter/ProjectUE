# ProjectUE

A comprehensive project management and onboarding system with AI-powered onboarding generation.

## Features

- **AI-Powered Onboarding**: Generate comprehensive, personalized onboarding plans using Together AI
- **Document Processing**: Upload and process PDF, Markdown, HTML, and text documents
- **Project Management**: Manage projects, tasks, and team members
- **Role-Based Access**: Secure user management with role-based permissions
- **Real-time Updates**: Live progress tracking and status updates

## Quick Start

1. **Clone the repository**
2. **Set up environment variables** (see `env.example`)
3. **Run with Docker**: `docker-compose up -d`
4. **Access the application**: http://localhost:8000

## Documentation

For detailed information about the LLM integration and AI-powered onboarding features, see:
- **[LLM Integration Guide](docs/LLM_INTEGRATION_GUIDE.md)** - Complete guide to AI onboarding generation

## Technology Stack

- **Backend**: Django 4.2, PostgreSQL, Redis
- **AI Integration**: Together AI API
- **Document Processing**: PyPDF2, BeautifulSoup, Markdown
- **Async Processing**: Celery, Redis
- **Frontend**: Django Templates, Bootstrap
- **Deployment**: Docker, Docker Compose
 
