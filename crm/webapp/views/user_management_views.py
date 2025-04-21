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
@user_passes_test(lambda u: u.is_superuser)
def manage_users(request):
    users = User.objects.all().order_by('username')
    roles = UserRole.objects.all()
    role_form = CreateRoleForm()

    # obsługa formularza tworzenia roli
    if request.method == 'POST':
        if 'create_role' in request.POST:
            role_form = CreateRoleForm(request.POST)
            if role_form.is_valid():
                role_form.save()
                messages.success(request, "New role created successfully.")
                return redirect('manage_users')
        elif 'assign_role' in request.POST:
            user_id = request.POST.get('user_id')
            role_id = request.POST.get('role_id')
            user = get_object_or_404(User, id=user_id)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role_id = role_id if role_id else None
            profile.save()
            messages.success(request, f"Updated role for {user.username}")
            return redirect('manage_users')
        elif 'edit_role_id' in request.POST:
            role = get_object_or_404(UserRole, id=request.POST.get("edit_role_id"))
            role.can_manage_users = 'can_manage_users' in request.POST
            role.can_manage_projects = 'can_manage_projects' in request.POST
            role.can_view_statistics = 'can_view_statistics' in request.POST
            role.save()
            messages.success(request, f"Permissions updated for role '{role.name}'.")
            return redirect('manage_users')

    user_profiles = [
    {
        'user': u,
        'profile': UserProfile.objects.get_or_create(user=u)[0]
    }
    for u in users
    ]

    context = {
        'users': users,
        'roles': roles,
        'role_form': role_form,
        'user_profiles': user_profiles,
    }
    return render(request, 'webapp/manage_users.html', context)