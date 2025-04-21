from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class UserRole(models.Model):
    name = models.CharField(max_length=50, unique=True)

    # Custom permissions for this role
    can_manage_users = models.BooleanField(default=False)
    can_manage_projects = models.BooleanField(default=False)
    can_view_statistics = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    role = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role.name if self.role else 'No Role'}"
    
    def has_permission(self, perm_name):
        if self.role:
            return getattr(self.role, perm_name, False)
        return False

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
