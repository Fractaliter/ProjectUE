from django.db import models
from django.contrib.auth.models import User
from .project_models import Project

class BaseTask(models.Model):
    class TaskStatus(models.TextChoices):
        TODO = 'todo', 'To Do'
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'

    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='base_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.TODO)

    class Meta:
        abstract = False

    def __str__(self):
        return self.title

class ProjectTask(BaseTask):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    duration = models.IntegerField(default=1)
