import csv
from django.shortcuts import render, redirect, get_object_or_404
from webapp.forms import (CreateUserForm, LoginForm, CreateContactForm, ContactForm, UpdateContactForm, TaskForm, ProjectForm, CreateRoleForm,
                    AssignProjectRoleForm, AddMemberForm, CreateProjectRoleForm, CreateOnboardingTaskForm,UpdateProgressForm,CreateOnboardingTaskTemplateForm, CreateOnboardingStepForm)
from django.db.models import Count, Sum
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from webapp.models import Contact, Project, ProjectTask, User,UserProfile, UserRole, ProjectRole, ProjectMembership, OnboardingStep, OnboardingTaskTemplate, OnboardingTask, OnboardingProgress
from django.contrib import messages
from webapp.spotify_utils import get_artist_info
from django.http import HttpResponse

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_to = request.user
            task.save()
            return redirect('task_detail', task_id=task.id)
    else:
        form = TaskForm()
    return render(request, 'webapp/task_form.html', {'form': form})


def task_list(request):
    tasks = ProjectTask.objects.all()
    return render(request, 'webapp/task_list.html', {'tasks': tasks})


def task_detail(request, task_id):
    task = get_object_or_404(ProjectTask, pk=task_id)
    return render(request, 'webapp/task_detail.html', {'task': task})

@login_required(login_url='my-login')
def task_dashboard(request):
    my_tasks = ProjectTask.objects.filter(assigned_to=request.user)

    # tylko projekty, gdzie user jest członkiem
    my_memberships = ProjectMembership.objects.filter(user=request.user).select_related('project')
    my_projects = [m.project for m in my_memberships]

    context = {
        'tasks': my_tasks,
        'projects': my_projects,
        'memberships': my_memberships,
    }
    return render(request, 'webapp/task_dashboard.html', context=context)


@login_required
def mark_task_complete(request, task_id):
    task = get_object_or_404(OnboardingTask, id=task_id, membership__user=request.user)
    task.status = OnboardingTask.TaskStatus.COMPLETED
    task.completed_at = timezone.now()
    task.completed = True
    task.save()
    messages.success(request, f"Marked task '{task.title}' as completed.")
    return redirect("onboarding_dashboard", membership_id=task.membership.id)

@login_required
def mark_task_in_progress(request, task_id):
    task = get_object_or_404(OnboardingTask, id=task_id, membership__user=request.user)
    task.status = OnboardingTask.TaskStatus.IN_PROGRESS
    task.completed = False
    task.completed_at = None
    task.save()
    messages.info(request, f"Task '{task.title}' marked as in progress.")
    return redirect("onboarding_dashboard", membership_id=task.membership.id)

@login_required
def reset_task_to_do(request, task_id):
    task = get_object_or_404(OnboardingTask, id=task_id, membership__user=request.user)
    task.status = OnboardingTask.TaskStatus.TODO
    task.completed = False
    task.completed_at = None
    task.save()
    messages.warning(request, f"Task '{task.title}' reset to To Do.")
    return redirect("onboarding_dashboard", membership_id=task.membership.id)


@login_required
def add_custom_task(request, membership_id, step_id):
    membership = get_object_or_404(ProjectMembership, id=membership_id, user=request.user)
    step = get_object_or_404(OnboardingStep, id=step_id, role=membership.role)

    if request.method == "POST":
        title = request.POST.get("title")
        if title:
            template = OnboardingTaskTemplate.objects.create(
                step=step,
                title=title,
                created_by=request.user,
                is_custom=True,
            )
            OnboardingTask.objects.create(
                membership=membership,
                step=step,
                template=template,
                assigned_by=request.user,
            )
            messages.success(request, "Custom task added.")
        return redirect("onboarding_progress", membership_id=membership.id)
