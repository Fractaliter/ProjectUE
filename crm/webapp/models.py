from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# -- Globalna rola użytkownika w aplikacji --
class UserRole(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    role = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role.name if self.role else 'No Role'}"


class Contact(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contact'
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=255)
    province = models.CharField(max_length=200)
    country = models.CharField(max_length=125)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# -- Projekt --
class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# -- Bazowa klasa zadania (dziedziczona przez różne typy) --
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


# -- Zadanie projektowe --
class ProjectTask(BaseTask):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    duration = models.IntegerField(default=1)


# -- Role projektowe i onboarding --
class ProjectRole(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.name} @ {self.project.name}"


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


class ProjectMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    role = models.ForeignKey(ProjectRole, on_delete=models.SET_NULL, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f"{self.user.username} in {self.project.name} as {self.role.name if self.role else 'Unassigned'}"

    def is_onboarding_completed(self):
        total = OnboardingTaskTemplate.objects.filter(step__role=self.role).count()
        done = self.user_onboarding_tasks.filter(completed=True).count()
        return total > 0 and done == total


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
