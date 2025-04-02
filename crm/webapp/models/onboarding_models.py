from django.db import models
from .project_models import ProjectRole, ProjectMembership
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
