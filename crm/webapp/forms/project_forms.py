from django import forms
from django.contrib.auth.models import User
from webapp.models import Project, UserRole, ProjectRole, ProjectMembership

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        
class CreateProjectForm(forms.ModelForm):
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

class AssignProjectRoleForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())
    role = forms.ModelChoiceField(queryset=ProjectRole.objects.all(), required=False)

class AddMemberForm(forms.ModelForm):
    project_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = ProjectMembership
        fields = ['user', 'role']

class CreateProjectRoleForm(forms.ModelForm):
    project_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = ProjectRole
        fields = ['name', 'description']
