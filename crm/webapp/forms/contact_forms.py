from django import forms
from webapp.models import Contact

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        exclude = ['user']

class CreateContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        exclude = ['user']
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'city', 'province', 'country']

class UpdateContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        exclude = ['user']
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'city', 'province', 'country']
