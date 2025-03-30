from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django import forms
from django.forms.widgets import PasswordInput, TextInput

from .models import Contact, ProjectTask, Project,UserProfile,UserRole

# - Register/Create a user
class CreateUserForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


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


class TaskForm(forms.ModelForm):
    class Meta:
        model = ProjectTask
        fields = ['title', 'description', 'date', 'time', 'project', 'duration']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']

class CreateRoleForm(forms.ModelForm):
    class Meta:
        model = UserRole
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Role name', 'class': 'form-control'})
        }