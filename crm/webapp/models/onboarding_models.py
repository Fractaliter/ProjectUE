from django.db import models
from .project_models import ProjectRole, ProjectMembership, Project
from django.contrib.auth.models import User
from .task_models import BaseTask

class OnboardingStep(models.Model):
    role = models.ForeignKey(ProjectRole, on_delete=models.CASCADE, related_name='steps')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.role.name})"

class OnboardingTaskTemplate(models.Model):
    step = models.ForeignKey(OnboardingStep, on_delete=models.CASCADE, related_name='task_templates')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    
    # LLM-assisted fields
    acceptance_criteria = models.TextField(null=True, blank=True, help_text="Kryteria akceptacji (bullet list)")
    estimated_time_hours = models.FloatField(null=True, blank=True, help_text="Szacowany czas w godzinach")
    source_context_ids = models.JSONField(null=True, blank=True, help_text="IDs fragmentów z RAG/dokumentacji")
    depends_on = models.JSONField(null=True, blank=True, help_text="Lista ID zadań, od których zależy ten task")

    def __str__(self):
        return f"{self.title} - {self.step.title}"

class OnboardingTask(BaseTask):
    template = models.ForeignKey(OnboardingTaskTemplate, on_delete=models.CASCADE)
    membership = models.ForeignKey(ProjectMembership, on_delete=models.CASCADE, related_name='user_onboarding_tasks')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    added_by_user = models.BooleanField(default=False)

    class Meta:
        unique_together = ('template', 'membership')

    def __str__(self):
        return f"{self.title} by {self.membership.user.username}"

class OnboardingProgress(models.Model):
    membership = models.ForeignKey(ProjectMembership, on_delete=models.CASCADE, related_name='onboarding_progress')
    task = models.ForeignKey(OnboardingTask, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('membership', 'task')

class OnboardingTemplateVersion(models.Model):
    """Wersjonowanie i audyt wygenerowanych szablonów onboardingowych"""
    step = models.ForeignKey(OnboardingStep, on_delete=models.CASCADE, related_name='versions')
    version = models.IntegerField(default=1)
    llm_model = models.CharField(max_length=100, help_text="Nazwa użytego modelu LLM")
    prompt_hash = models.CharField(max_length=64, help_text="Hash promptu dla audytu")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    changelog = models.TextField(help_text="Opis zmian w wersji")
    draft_data = models.JSONField(null=True, blank=True, help_text="Draft JSON przed zatwierdzeniem")
    is_active = models.BooleanField(default=False, help_text="Czy wersja jest aktywna")
    
    class Meta:
        unique_together = ('step', 'version')
        ordering = ['-version']
    
    def __str__(self):
        return f"{self.step.title} v{self.version} ({self.llm_model})"

class DocumentSource(models.Model):
    """Dokumenty źródłowe do generowania onboardingu"""
    
    # AI Generation Status choices
    AI_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='onboarding_docs/', null=True, blank=True)
    content = models.TextField(help_text="Ekstraktowana treść dokumentu")
    doc_type = models.CharField(max_length=20, choices=[
        ('pdf', 'PDF'),
        ('md', 'Markdown'),
        ('html', 'HTML'),
        ('txt', 'Text'),
    ])
    url = models.URLField(null=True, blank=True, help_text="Link do dokumentu zewnętrznego")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # AI Generation Status fields
    ai_generation_status = models.CharField(
        max_length=20, 
        choices=AI_STATUS_CHOICES, 
        default='pending',
        help_text="Status of AI processing for this document"
    )
    ai_processing_started_at = models.DateTimeField(null=True, blank=True)
    ai_processing_completed_at = models.DateTimeField(null=True, blank=True)
    ai_processing_error = models.TextField(null=True, blank=True, help_text="Error message if processing failed")
    ai_processing_progress = models.IntegerField(default=0, help_text="Processing progress percentage (0-100)")
    
    def __str__(self):
        return f"{self.title} ({self.project.name})"
