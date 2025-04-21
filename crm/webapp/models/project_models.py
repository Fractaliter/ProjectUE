from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)

    def is_user_admin(self, user):
        return self.memberships.filter(user=user, is_admin=True).exists()
    
    def __str__(self):
        return self.name

class ProjectRole(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.name} @ {self.project.name}"

class ProjectMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    role = models.ForeignKey(ProjectRole, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin = models.BooleanField(default=False)  # NEW
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f"{self.user.username} in {self.project.name} as {self.role.name if self.role else 'Unassigned'}"

    def is_onboarding_completed(self):
        from .onboarding_models import OnboardingTaskTemplate  # zapobiegamy cyklom
        total = OnboardingTaskTemplate.objects.filter(step__role=self.role).count()
        done = self.user_onboarding_tasks.filter(completed=True).count()
        return total > 0 and done == total
