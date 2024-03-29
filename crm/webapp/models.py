from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Contact(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # This references the currently active user model
        on_delete=models.CASCADE,  # Ensures that the contact is deleted when the user is deleted
        related_name='contact'     # Allows you to access the contact from the User model easily
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

        return self.first_name + "   " + self.last_name

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=200)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.title
    
class Attendee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.user.username} - {self.event.title}"















