from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Contact,Event

from django import forms

from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import PasswordInput, TextInput

# - Register/Create a user

class CreateUserForm(UserCreationForm):

    class Meta:

        model = User
        fields = ['username', 'password1', 'password2']


# - Login a user

class LoginForm(AuthenticationForm):

    username = forms.CharField(widget=TextInput())
    password = forms.CharField(widget=PasswordInput())

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        exclude = ['user']
        
# - Create a contact

class CreateContactForm(forms.ModelForm):

    class Meta:

        model = Contact
        exclude = ['user']
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'city', 'province', 'country']


# - Update a contact

class UpdateContactForm(forms.ModelForm):

    class Meta:

        model = Contact
        exclude = ['user']
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'city', 'province', 'country']

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'time', 'location'] 
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }
