"""
Views dla LLM-assisted onboarding
"""
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib import messages
from webapp.models import (
    Project, ProjectRole, OnboardingStep, OnboardingTaskTemplate,
    OnboardingTemplateVersion, DocumentSource, ProjectMembership
)
from webapp.llm_service import (
    generate_onboarding_draft,
    validate_and_fix_draft,
    extract_text_from_document,
    process_documents_with_status,
    chunk_text,
    update_document_status
)

logger = logging.getLogger(__name__)


def is_project_admin(user, project):
    """Sprawdza czy użytkownik jest adminem projektu"""
    return ProjectMembership.objects.filter(
        user=user,
        project=project,
        is_admin=True
    ).exists()


@login_required
def llm_onboarding_generate(request, project_id):
    """
    Główny widok do generowania draftu onboardingu przez LLM.
    
    GET: Wyświetla formularz
    POST: Generuje draft i przekierowuje do review
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Sprawdzenie uprawnień
    is_admin = is_project_admin(request.user, project)
    if not is_admin:
        # Show the page but with admin error flag
        roles = ProjectRole.objects.filter(project=project)
        documents = DocumentSource.objects.filter(project=project)
        context = {
            'project': project,
            'roles': roles,
            'documents': documents,
            'show_admin_error': True,
            'is_admin': False
        }
        return render(request, 'webapp/llm_onboarding_generate.html', context)
    
    roles = ProjectRole.objects.filter(project=project)
    documents = DocumentSource.objects.filter(project=project)
    
    if request.method == 'POST':
        try:
            role_id = request.POST.get('role_id')
            project_stack = request.POST.get('project_stack', '')
            doc_ids = request.POST.getlist('document_ids')
            
            if not role_id:
                messages.error(request, "Please select a role")
                return redirect('llm_onboarding_generate', project_id=project_id)
            
            role = get_object_or_404(ProjectRole, id=role_id, project=project)
            
            # Process documents with status tracking
            if doc_ids:
                # Convert string IDs to integers
                doc_ids_int = [int(doc_id) for doc_id in doc_ids if doc_id.isdigit()]
                
                # Process documents with status tracking
                logger.info(f"Processing {len(doc_ids_int)} documents for project {project.name}, role {role.name}")
                result = process_documents_with_status(
                    document_ids=doc_ids_int,
                    role_name=role.name,
                    project_stack=project_stack or f"{project.name} project"
                )
            else:
                # If no documents selected, use placeholder
                documentation_chunks = [
                    f"Project: {project.name}\n"
                    f"Stack: {project_stack}\n"
                    f"Role: {role.name}\n"
                    "This is a standard software development project."
                ]
                
                # Generate draft without status tracking
                logger.info(f"Generating onboarding for project {project.name}, role {role.name} without documents")
                result = generate_onboarding_draft(
                    role_name=role.name,
                    project_stack=project_stack or f"{project.name} project",
                    documentation_chunks=documentation_chunks
                )
            
            if not result['success']:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Generation failed: {error_msg}")
                messages.error(request, f"Generation error: {error_msg}")
                return redirect('llm_onboarding_generate', project_id=project_id)
            
            # Check if result has data key (direct generation or document processing)
            # Document processing returns 'draft_data', direct generation returns 'data'
            if 'data' in result:
                draft_data_raw = result['data']
            elif 'draft_data' in result:
                draft_data_raw = result['draft_data']
            else:
                logger.error(f"No data in result: {result.keys()}")
                messages.error(request, "Generation failed - no data returned")
                return redirect('llm_onboarding_generate', project_id=project_id)
            
            # Log success
            logger.info(f"Generation successful, validating draft...")
            
            # Walidacja i naprawa draftu
            draft_data = validate_and_fix_draft(draft_data_raw)
            
            # Additional validation
            if not draft_data.get('steps') or not draft_data.get('tasks'):
                logger.error(f"Invalid draft data - missing steps or tasks")
                messages.error(request, "Generated plan is invalid - please try again")
                return redirect('llm_onboarding_generate', project_id=project_id)
            
            # Zapisz draft w sesji (tymczasowo)
            request.session['llm_draft'] = {
                'project_id': project_id,
                'role_id': role_id,
                'draft_data': draft_data,
                'metadata': result['metadata']
            }
            
            messages.success(request, f"✅ Generated {len(draft_data['steps'])} steps and {len(draft_data['tasks'])} tasks")
            return redirect('llm_onboarding_review', project_id=project_id)
        
        except Exception as e:
            logger.error(f"Błąd podczas generowania onboardingu: {e}", exc_info=True)
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('llm_onboarding_generate', project_id=project_id)
    
    context = {
        'project': project,
        'roles': roles,
        'documents': documents,
        'show_admin_error': False,
        'is_admin': True,
        'use_async': True  # Flag to enable async generation
    }
    return render(request, 'webapp/llm_onboarding_generate.html', context)


@login_required
def llm_onboarding_review(request, project_id):
    """
    Widok do review i edycji wygenerowanego draftu.
    
    GET: Wyświetla draft do edycji
    POST: Zatwierdza i zapisuje do bazy
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Sprawdzenie uprawnień
    if not is_project_admin(request.user, project):
        messages.error(request, "No permissions")
        return redirect('onboarding_setup', project_id=project_id)
    
    # Pobierz draft z sesji
    draft_session = request.session.get('llm_draft')
    if not draft_session or draft_session.get('project_id') != project_id:
        messages.error(request, "No draft to review. Generate a new one.")
        return redirect('llm_onboarding_generate', project_id=project_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'reject':
            # Odrzuć draft
            del request.session['llm_draft']
            messages.info(request, "Draft rejected")
            return redirect('llm_onboarding_generate', project_id=project_id)
        
        elif action == 'approve':
            try:
                # Zatwierdzenie draftu i zapis do bazy
                with transaction.atomic():
                    role_id = draft_session['role_id']
                    role = get_object_or_404(ProjectRole, id=role_id)
                    draft_data = draft_session['draft_data']
                    metadata = draft_session['metadata']
                    
                    # Tworzymy steps i tasks
                    step_map = {}  # ID z draftu -> instancja OnboardingStep
                    
                    for step_data in draft_data['steps']:
                        step = OnboardingStep.objects.create(
                            role=role,
                            title=step_data['title'],
                            description=step_data.get('description', ''),
                            order=step_data.get('order', 1)
                        )
                        step_map[step_data['id']] = step
                        
                        # Utworzenie wersji dla audytu
                        OnboardingTemplateVersion.objects.create(
                            step=step,
                            version=1,
                            llm_model=metadata['llm_model'],
                            prompt_hash=metadata['prompt_hash'],
                            created_by=request.user,
                            changelog="Auto-generated via LLM, reviewed and approved by admin",
                            draft_data=draft_data,
                            is_active=True
                        )
                    
                    # Tworzymy tasks
                    for task_data in draft_data['tasks']:
                        step_id = task_data['step_id']
                        step = step_map.get(step_id)
                        
                        if not step:
                            logger.warning(f"Step {step_id} not found for task {task_data['title']}")
                            continue
                        
                        OnboardingTaskTemplate.objects.create(
                            step=step,
                            title=task_data['title'],
                            description=task_data.get('description', ''),
                            is_required=task_data.get('is_required', True),
                            acceptance_criteria='\n'.join(task_data.get('acceptance_criteria', [])),
                            estimated_time_hours=task_data.get('estimated_time_hours'),
                            depends_on=task_data.get('depends_on', [])
                        )
                    
                    # Usuwamy draft z sesji
                    del request.session['llm_draft']
                    
                    messages.success(request, f"✅ Onboarding for role '{role.name}' saved successfully!")
                    return redirect('onboarding_setup', project_id=project_id)
            
            except Exception as e:
                logger.error(f"Błąd podczas zatwierdzania draftu: {e}", exc_info=True)
                messages.error(request, f"Save error: {str(e)}")
    
    # Przygotuj dane do wyświetlenia
    draft_data = draft_session['draft_data']
    role = get_object_or_404(ProjectRole, id=draft_session['role_id'])
    
    context = {
        'project': project,
        'role': role,
        'steps': draft_data['steps'],
        'tasks': draft_data['tasks'],
        'metadata': draft_session['metadata'],
    }
    return render(request, 'webapp/llm_onboarding_review.html', context)


@login_required
@require_http_methods(["POST"])
def llm_onboarding_edit_draft(request, project_id):
    """
    API endpoint do edycji draftu (AJAX).
    Pozwala na modyfikację draftu przed zatwierdzeniem.
    """
    project = get_object_or_404(Project, id=project_id)
    
    if not is_project_admin(request.user, project):
        return JsonResponse({'error': 'Brak uprawnień'}, status=403)
    
    try:
        data = json.loads(request.body)
        draft_session = request.session.get('llm_draft')
        
        if not draft_session or draft_session.get('project_id') != project_id:
            return JsonResponse({'error': 'Brak aktywnego draftu'}, status=400)
        
        # Aktualizuj draft
        draft_session['draft_data'] = data.get('draft_data', draft_session['draft_data'])
        request.session['llm_draft'] = draft_session
        request.session.modified = True
        
        return JsonResponse({'success': True, 'message': 'Draft zaktualizowany'})
    
    except Exception as e:
        logger.error(f"Błąd podczas edycji draftu: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def upload_document(request, project_id):
    """
    Upload dokumentu źródłowego dla projektu.
    """
    project = get_object_or_404(Project, id=project_id)
    
    if not is_project_admin(request.user, project):
        messages.error(request, "No permissions")
        return redirect('onboarding_setup', project_id=project_id)
    
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            doc_type = request.POST.get('doc_type', 'txt')
            content = request.POST.get('content', '')
            url = request.POST.get('url', '')
            
            uploaded_file = request.FILES.get('file')
            
            if uploaded_file:
                # Odczytaj zawartość pliku
                content = uploaded_file.read().decode('utf-8')
            
            DocumentSource.objects.create(
                project=project,
                title=title,
                content=content,
                doc_type=doc_type,
                url=url,
                uploaded_by=request.user
            )
            
            messages.success(request, f"Document '{title}' has been added")
            return redirect('llm_onboarding_generate', project_id=project_id)
        
        except Exception as e:
            messages.error(request, f"Upload error: {str(e)}")
    
    context = {
        'project': project,
    }
    return render(request, 'webapp/upload_document.html', context)


@login_required
@require_http_methods(["GET"])
def document_status_api(request, project_id):
    """
    API endpoint to get document processing status.
    Returns JSON with status information for all documents in the project.
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Check permissions
    if not is_project_admin(request.user, project):
        return JsonResponse({'error': 'No permissions'}, status=403)
    
    # Get base queryset for documents
    base_qs = DocumentSource.objects.filter(project=project)
    
    # Get document details
    documents = base_qs.values(
        'id', 'title', 'ai_generation_status', 'ai_processing_progress',
        'ai_processing_started_at', 'ai_processing_completed_at', 'ai_processing_error'
    )
    
    return JsonResponse({
        'documents': list(documents),
        'total_documents': base_qs.count(),
        'status_summary': {
            'pending': base_qs.filter(ai_generation_status='pending').count(),
            'processing': base_qs.filter(ai_generation_status='processing').count(),
            'completed': base_qs.filter(ai_generation_status='completed').count(),
            'failed': base_qs.filter(ai_generation_status='failed').count(),
            'skipped': base_qs.filter(ai_generation_status='skipped').count(),
        }
    })


@login_required
@require_http_methods(["POST"])
def llm_onboarding_generate_sync(request, project_id):
    """
    Generate onboarding plan synchronously (Railway free tier compatible).
    Returns the generated plan directly.
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Check permissions
    if not is_project_admin(request.user, project):
        return JsonResponse({'error': 'No permissions'}, status=403)
    
    try:
        # Parse request data
        data = json.loads(request.body) if request.body else {}
        role_id = data.get('role_id') or request.POST.get('role_id')
        project_stack = data.get('project_stack', '') or request.POST.get('project_stack', '')
        doc_ids = data.get('document_ids', []) or request.POST.getlist('document_ids')
        
        if not role_id:
            return JsonResponse({'error': 'No role selected'}, status=400)
        
        role = get_object_or_404(ProjectRole, id=role_id, project=project)
        
        # Convert doc IDs to integers
        doc_ids_int = [int(doc_id) for doc_id in doc_ids if str(doc_id).isdigit()]
        
        # Process documents if provided
        documentation_chunks = []
        if doc_ids_int:
            logger.info(f"Processing {len(doc_ids_int)} documents for project {project_id}")
            documents = DocumentSource.objects.filter(id__in=doc_ids_int)
            for doc in documents:
                try:
                    update_document_status(doc.id, 'processing', 25)
                    content = extract_text_from_document(doc.content, doc.doc_type)
                    if content:
                        chunks = chunk_text(content)
                        documentation_chunks.extend(chunks)
                    update_document_status(doc.id, 'processing', 50)
                except Exception as e:
                    logger.error(f"Error processing document {doc.id}: {e}")
                    update_document_status(doc.id, 'failed', 0, str(e))
        
        # Generate with LLM synchronously
        logger.info(f"Starting synchronous generation for project {project_id}, role {role_id}")
        result = generate_onboarding_draft(
            role_name=role.name,
            project_stack=project_stack or f"{project.name} project",
            documentation_chunks=documentation_chunks
        )
        
        # Mark documents as completed
        if doc_ids_int:
            for doc_id in doc_ids_int:
                update_document_status(doc_id, 'completed', 100)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'data': result['data'],
                'metadata': result['metadata'],
                'message': 'Generation completed successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'message': 'Generation failed'
            }, status=500)
        
    except Exception as e:
        logger.error(f"Error in synchronous generation: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


# Task status function removed - no longer needed with synchronous generation


