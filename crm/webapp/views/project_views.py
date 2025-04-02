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

@login_required
def manage_projects(request):
    projects = Project.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        project_id = request.POST.get('project_id')
        project = get_object_or_404(Project, id=project_id) if project_id else None

        if action == 'add_member':
            add_member_form = AddMemberForm(request.POST)
            if add_member_form.is_valid():
                membership = add_member_form.save(commit=False)
                membership.project = project
                membership.save()
                messages.success(request, f"{membership.user.username} added to project '{membership.project.name}' and onboarding tasks assigned.")
                return redirect('manage_projects')
            
        elif action == 'create_role':
            add_role_form = CreateProjectRoleForm(request.POST)
            if add_role_form.is_valid():
                role = add_role_form.save(commit=False)
                role.project = project
                role.save()
                return redirect('manage_projects')
            
        elif action == 'create_project':
            create_project_form = CreateProjectForm(request.POST)
            if create_project_form.is_valid():
                create_project_form.save()
                return redirect('manage_projects')
            
        elif action == 'delete_project' and project:
            project.delete()
            return redirect('manage_projects')
        
        elif action == 'delete_member':
            membership_id = request.POST.get('membership_id')
            ProjectMembership.objects.filter(id=membership_id).delete()
            return redirect('manage_projects')

        elif action == 'delete_role':
            role_id = request.POST.get('role_id')
            ProjectRole.objects.filter(id=role_id).delete()
            return redirect('manage_projects')

    # Przy GET albo jeśli POST nie był poprawny:
    add_member_form = AddMemberForm()
    add_role_form = CreateProjectRoleForm()
    create_project_form = CreateProjectForm()

    context = {
        'projects': projects,
        'add_member_form': add_member_form,
        'add_role_form': add_role_form,
        'create_project_form': create_project_form,
    }
    return render(request, 'webapp/manage_projects.html', context)

@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.creator = request.user
            project.save()
            return redirect('task_dashboard')
    else:
        form = ProjectForm()
    return render(request, 'webapp/project_form.html', {'form': form})