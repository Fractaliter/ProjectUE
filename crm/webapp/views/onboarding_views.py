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
def onboarding_progress(request, membership_id):
    membership = get_object_or_404(ProjectMembership, id=membership_id, user=request.user)
    steps = OnboardingStep.objects.filter(role=membership.role).order_by("order")
    tasks = OnboardingTask.objects.filter(membership=membership)

    task_lookup = {(t.step.id, t.template.id): t for t in tasks}

    structured = []
    for step in steps:
        templates = step.task_templates.all()
        step_tasks = []
        for tmpl in templates:
            task = task_lookup.get((step.id, tmpl.id))
            step_tasks.append({"template": tmpl, "task": task})
        structured.append({"step": step, "tasks": step_tasks})

    context = {
        "membership": membership,
        "structured_steps": structured,
    }
    return render(request, "webapp/onboarding_progress.html", context)


@login_required
def onboarding_setup(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    roles = ProjectRole.objects.filter(project=project)
    task_form = CreateOnboardingTaskTemplateForm()
    step_form = CreateOnboardingStepForm()

    if request.method == 'POST':
        if 'add_task' in request.POST:
            task_form = CreateOnboardingTaskTemplateForm(request.POST)
            if task_form.is_valid():
                task_form.save()
                messages.success(request, "Task added successfully.")
                return redirect('onboarding_setup', project_id=project_id)

        elif 'add_step' in request.POST:
            step_form = CreateOnboardingStepForm(request.POST)
            if step_form.is_valid():
                step_form.save()
                messages.success(request, "Step added successfully.")
                return redirect('onboarding_setup', project_id=project_id)

        elif 'delete_task' in request.POST:
            task_id = request.POST.get("task_id")
            OnboardingTaskTemplate.objects.filter(id=task_id).delete()
            messages.success(request, "Task deleted.")
            return redirect('onboarding_setup', project_id=project_id)

    context = {
        'project': project,
        'roles': roles,
        'task_form': task_form,
        'step_form': step_form,
    }
    return render(request, 'webapp/onboarding_setup.html', context)

@login_required
def onboarding_dashboard(request, membership_id):
    membership = get_object_or_404(ProjectMembership, id=membership_id, user=request.user)
    steps = OnboardingStep.objects.filter(role=membership.role).order_by('order')

    user_tasks = {
        task.template.id: task
        for task in OnboardingTask.objects.filter(membership=membership)
    }

    if request.method == 'POST':
        if 'complete_task_id' in request.POST:
            task_id = request.POST.get('complete_task_id')
            template = get_object_or_404(OnboardingTaskTemplate, id=task_id)
            task, _ = OnboardingTask.objects.get_or_create(
                membership=membership,
                template=template
            )
            task.completed = True
            task.completed_at = timezone.now()
            task.save()
            return redirect('onboarding_dashboard', membership_id=membership.id)

        elif 'custom_step_id' in request.POST:
            step_id = request.POST.get('custom_step_id')
            step = get_object_or_404(OnboardingStep, id=step_id, role=membership.role)
            form = CreateOnboardingTaskForm(request.POST)
            if form.is_valid():
                task = form.save(commit=False)
                task.membership = membership
                task.step = step
                task.save()
                return redirect('onboarding_dashboard', membership_id=membership.id)
    else:
        form = CreateOnboardingTaskForm()

    context = {
        'membership': membership,
        'onboarding_steps': steps,
        'user_tasks': user_tasks,
        'custom_task_form': form,
    }
    return render(request, 'webapp/onboarding_dashboard.html', context)

@login_required
def update_onboarding_progress(request, progress_id):
    progress = get_object_or_404(OnboardingProgress, id=progress_id, membership__user=request.user)

    if request.method == 'POST':
        form = UpdateProgressForm(request.POST, instance=progress)
        if form.is_valid():
            updated_progress = form.save(commit=False)
            if updated_progress.completed and not progress.completed_at:
                updated_progress.completed_at = timezone.now()
            updated_progress.save()
            return redirect('onboarding_dashboard', project_id=progress.membership.project.id)
    else:
        form = UpdateProgressForm(instance=progress)

    context = {'form': form, 'progress': progress}
    return render(request, 'webapp/update_onboarding_progress.html', context)

@login_required
def onboarding_projects(request):
    memberships = ProjectMembership.objects.filter(user=request.user).select_related('project', 'role')
    projects = [membership.project for membership in memberships]

    context = {
        'projects': projects,
        'memberships': memberships,
    }
    return render(request, 'webapp/onboarding_projects.html', context)
