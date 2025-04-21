import csv
from django.shortcuts import render, redirect, get_object_or_404
from webapp.forms import (CreateUserForm, LoginForm, CreateContactForm, ContactForm, UpdateContactForm, TaskForm, ProjectForm, CreateRoleForm,
                    AssignProjectRoleForm, AddMemberForm, CreateProjectRoleForm, CreateProjectForm, CreateOnboardingTaskForm,UpdateProgressForm,CreateOnboardingTaskTemplateForm, CreateOnboardingStepForm)
from django.db.models import Count, Sum
from django.utils import timezone
from django.contrib.auth.models import auth
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from webapp.models import Contact, Project, ProjectTask, User,UserProfile, UserRole, ProjectRole, ProjectMembership, OnboardingStep, OnboardingTaskTemplate, OnboardingTask, OnboardingProgress
from django.contrib import messages
from webapp.spotify_utils import get_artist_info
from django.http import HttpResponse


@login_required(login_url='my-login')
def contact_dashboard(request):
    contact_exists = Contact.objects.filter(user=request.user).exists()
    my_contacts = Contact.objects.filter(user=request.user)
    context = {'contacts': my_contacts, 'contact_exists': contact_exists}
    return render(request, 'webapp/contact_dashboard.html', context=context)

@login_required(login_url='my-login')
def create_contact(request):
    if request.method == "POST":
        form = CreateContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            messages.success(request, "Your contact was created!")
            return redirect("contact_dashboard")
    else:
        form = ContactForm()
    return render(request, 'webapp/create_contact.html', {'form': form})


@login_required(login_url='my-login')
def update_contact(request, pk):
    contact = Contact.objects.get(id=pk)
    form = UpdateContactForm(instance=contact)
    if request.method == 'POST':
        form = UpdateContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, "Your contact was updated!")
            return redirect("contact_dashboard")
    context = {'form': form}
    return render(request, 'webapp/update_contact.html', context=context)


@login_required(login_url='my-login')
def singular_contact(request, pk):
    all_contacts = Contact.objects.get(id=pk)
    context = {'contact': all_contacts}
    return render(request, 'webapp/view_contact.html', context=context)


@login_required(login_url='my-login')
def delete_contact(request, pk):
    contact = Contact.objects.get(id=pk)
    contact.delete()
    messages.success(request, "Your contact was deleted!")
    return redirect("contact_dashboard")