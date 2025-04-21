from django import forms
from webapp.models import OnboardingTask, OnboardingProgress, OnboardingTaskTemplate, OnboardingStep

class CreateOnboardingTaskForm(forms.ModelForm):
    class Meta:
        model = OnboardingTask
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter custom task title'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter details...'}),
        }

class UpdateProgressForm(forms.ModelForm):
    class Meta:
        model = OnboardingProgress
        fields = ['completed']

class CreateOnboardingTaskTemplateForm(forms.ModelForm):
    class Meta:
        model = OnboardingTaskTemplate
        fields = ['step', 'title', 'description', 'is_required']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Task title'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class CreateOnboardingStepForm(forms.ModelForm):
    class Meta:
        model = OnboardingStep
        fields = ['role', 'title', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Step title'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }
