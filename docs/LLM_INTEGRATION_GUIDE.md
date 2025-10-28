# 🤖 LLM Integration Guide

## Overview

This project uses AI-powered onboarding generation to create comprehensive, personalized onboarding plans for new team members. The system leverages Together AI's API for intelligent content generation with a robust template-based fallback.

## Architecture

### Primary: Together AI API
- **Model**: Configurable via `TOGETHER_MODEL` environment variable
- **Default**: `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` (fast, good quality)
- **Speed**: 2-5 seconds (varies by model)
- **Quality**: High-quality, context-aware generation
- **Reliability**: 95%+ success rate

### Fallback: Template-Based Generation
- **Method**: Comprehensive 10-step template
- **Speed**: Instant
- **Quality**: Reliable, structured output
- **Coverage**: 20+ detailed tasks across all domains

## Features

### 🎯 **Comprehensive Onboarding Plans**
- **8-12 detailed steps** (vs old 3-4 basic steps)
- **15-20 specific tasks** with clear acceptance criteria
- **Time estimates** for each task
- **Dependencies** and prerequisites
- **Role-specific** content based on project stack

### 📚 **Document Processing**
- **Multi-format support**: PDF, Markdown, HTML, TXT
- **Content extraction** and chunking
- **Context-aware** generation using uploaded docs
- **Progress tracking** for document processing

### 🔄 **Generation Flow**
```
1. User uploads documents + selects role
2. System processes documents (PDF → text → chunks)
3. Together AI generates comprehensive plan (8-12 steps)
4. If AI fails → Template fallback (10 steps, 20 tasks)
5. User reviews and approves plan
6. Plan becomes active onboarding template
```

## Setup

### Environment Variables
```bash
# Together AI (Primary)
TOGETHER_API_KEY=your_together_api_key
TOGETHER_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

### Available Models
| Model | Speed | Quality | Cost | Best For |
|-------|-------|---------|------|----------|
| `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` | Fast | Good | Low | Quick iterations, development |
| `meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo` | Slower | Excellent | Higher | Production, complex tasks |
| `mistralai/Mixtral-8x7B-Instruct-v0.1` | Medium | Very Good | Medium | Balanced performance |
| `Qwen/Qwen2.5-72B-Instruct` | Slower | Excellent | Higher | High-quality output |

### Dependencies
```txt
# Core Django
Django==4.2
django-crispy-forms==1.14.0

# Database
psycopg2-binary==2.9.9

# Document Processing
PyPDF2==3.0.1
markdown==3.5.1
beautifulsoup4==4.12.2
lxml==4.9.3

# Async Processing
celery==5.3.4
redis==5.0.3

# API Integration
requests==2.31.0
```

## Usage

### 1. Generate Onboarding Plan
```python
from webapp.llm_service import generate_onboarding_draft

result = generate_onboarding_draft(
    role_name="Backend Developer (Django)",
    project_stack="Django 4.2, PostgreSQL, Redis, Docker",
    documentation_chunks=["Your onboarding documentation..."]
)

if result['success']:
    steps = result['data']['steps']  # 8-12 comprehensive steps
    tasks = result['data']['tasks']  # 15-20 detailed tasks
```

### 2. Process Documents
```python
from webapp.llm_service import process_documents_with_status

result = process_documents_with_status(
    document_ids=[1, 2, 3],
    role_name="Frontend Developer",
    project_stack="React, TypeScript, Vite"
)
```

## Generated Content Structure

### Steps (8-12 comprehensive phases)
1. **Environment Setup** - Development tools and dependencies
2. **Development Tools Configuration** - IDE, linters, formatters
3. **Project Architecture Overview** - Codebase structure and modules
4. **Database and Data Layer** - Database setup and models
5. **Authentication and Permissions** - User roles and RBAC
6. **API and Integration Setup** - External services and APIs
7. **Testing Framework** - Testing environment and practices
8. **CI/CD and Deployment** - Build and deployment processes
9. **Code Review and Standards** - Coding standards and review process
10. **Documentation and Knowledge Transfer** - Final knowledge sharing

### Tasks (15-20 detailed actions)
Each step contains 2-4 specific tasks with:
- **Clear descriptions** and acceptance criteria
- **Time estimates** (1-4 hours per task)
- **Dependencies** and prerequisites
- **Required vs optional** classification

## API Endpoints

### Generate Onboarding
```
POST /projects/{project_id}/llm-onboarding/generate/
- role_id: ProjectRole ID
- project_stack: Technology stack description
- document_ids: Array of DocumentSource IDs
```

### Review Generated Plan
```
GET /projects/{project_id}/llm-onboarding/review/
- Shows generated steps and tasks
- Allows editing before approval
```

### Upload Documents
```
POST /projects/{project_id}/llm-onboarding/upload/
- file: Document file (PDF, MD, HTML, TXT)
- title: Document title
- doc_type: File type
```

## Error Handling

### Together AI Failures
- **Automatic fallback** to template-based generation
- **No user interruption** - seamless experience
- **Comprehensive output** still provided (10 steps, 20 tasks)

### Document Processing Errors
- **Individual document tracking** - failed docs don't block others
- **Progress indicators** - real-time status updates
- **Error logging** - detailed error messages for debugging

### JSON Parsing Issues
- **Multi-tier repair** - aggressive JSON repair strategies
- **Robust parsing** - handles malformed LLM output
- **Fallback validation** - ensures valid structure

## Performance

### Generation Speed
- **Together AI**: 2-5 seconds
- **Template Fallback**: <1 second
- **Document Processing**: 1-3 seconds per document

### Resource Usage
- **Memory**: Minimal (no local models)
- **CPU**: Low (API-based)
- **Storage**: Only document content and generated plans

## Monitoring

### Logs
```python
# Generation success
logger.info(f"Together AI succeeded! Generated {len(output)} characters")

# Fallback usage
logger.info("Using template-based generation fallback...")

# Document processing
logger.info(f"Processing {len(doc_ids)} documents for project {project.name}")
```

### Status Tracking
- **Document status**: pending → processing → completed/failed
- **Generation progress**: 10% → 50% → 75% → 100%
- **Error messages**: Detailed error logging for debugging

## Best Practices

### 1. Document Preparation
- **Upload comprehensive docs** - better context = better generation
- **Use clear, structured content** - numbered lists, sections
- **Include specific instructions** - installation steps, configurations

### 2. Role Definition
- **Be specific** - "Backend Developer (Django)" vs "Developer"
- **Include technology stack** - helps AI understand context
- **Provide project context** - company-specific requirements

### 3. Review Process
- **Always review generated plans** - AI is good but not perfect
- **Edit as needed** - add/remove/modify steps and tasks
- **Test with real users** - validate effectiveness

## Troubleshooting

### Common Issues

#### "Invalid draft data - missing steps or tasks"
- **Cause**: JSON parsing failed, fallback didn't work
- **Solution**: Check logs for parsing errors, verify Together AI API key

#### "Document processing failed"
- **Cause**: Unsupported file format or corrupted file
- **Solution**: Use supported formats (PDF, MD, HTML, TXT), check file integrity

#### "Together AI API failed"
- **Cause**: API key invalid, rate limits, or service down
- **Solution**: Verify API key, check Together AI status, system falls back automatically

### Debug Mode
```python
# Enable detailed logging
import logging
logging.getLogger('webapp.llm_service').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
- **Multi-language support** - generate plans in different languages
- **Custom templates** - user-defined step templates
- **Integration with HR systems** - automatic role assignment
- **Analytics dashboard** - track onboarding effectiveness
- **AI model selection** - choose between different LLM models

### Performance Improvements
- **Caching** - cache generated plans for similar roles
- **Batch processing** - generate multiple plans simultaneously
- **Async document processing** - process large documents in background

---

## Quick Start

1. **Set up environment variables** (Together AI API key)
2. **Upload onboarding documents** to your project
3. **Create project roles** (Backend Developer, Frontend Developer, etc.)
4. **Generate onboarding plan** - select role and documents
5. **Review and approve** the generated plan
6. **Assign to new team members** - they get personalized onboarding tasks

The system will automatically generate comprehensive, role-specific onboarding plans that cover all aspects of getting new team members up to speed! 🚀
