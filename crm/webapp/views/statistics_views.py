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
def statistics_dashboard(request):
    projects = Project.objects.all()
    organizers = User.objects.all()
    selected_project = request.GET.get('project')
    selected_organizer = request.GET.get('organizer')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    tasks = ProjectTask.objects.all()
    if selected_project:
        tasks = tasks.filter(project_id=selected_project)
    if selected_organizer:
        tasks = tasks.filter(assigned_to_id=selected_organizer)
    if start_date:
        tasks = tasks.filter(date__gte=start_date)
    if end_date:
        tasks = tasks.filter(date__lte=end_date)

    task_count_by_project = ProjectTask.objects.values('project__name').annotate(total=Count('id')).order_by('-total')
    task_count_by_organizer = ProjectTask.objects.values('assigned_to__username').annotate(total=Count('id')).order_by('-total')
    task_stats_by_project = ProjectTask.objects.values('project__name').annotate(
        total_tasks=Count('id'),
        total_duration=Sum('duration')
    ).order_by('-total_tasks')

    total_duration = tasks.aggregate(Sum('duration'))['duration__sum'] or 0

    context = {
        'projects': projects,
        'organizers': organizers,
        'tasks': tasks,
        'task_count_by_project': task_count_by_project,
        'task_count_by_organizer': task_count_by_organizer,
        'task_stats_by_project': task_stats_by_project,
        'selected_project': selected_project,
        'selected_organizer': selected_organizer,
        'start_date': start_date,
        'end_date': end_date,
        'total_duration': total_duration
    }
    return render(request, 'webapp/statistics_dashboard.html', context)


def export_tasks_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="filtered_tasks.csv"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Description', 'Date', 'Time', 'Project', 'Duration', 'Assigned To'])

    tasks = ProjectTask.objects.all()

    if request.GET.get('project'):
        tasks = tasks.filter(project_id=request.GET['project'])
    if request.GET.get('organizer'):
        tasks = tasks.filter(assigned_to_id=request.GET['organizer'])
    if request.GET.get('start_date'):
        tasks = tasks.filter(date__gte=request.GET['start_date'])
    if request.GET.get('end_date'):
        tasks = tasks.filter(date__lte=request.GET['end_date'])

    for task in tasks:
        writer.writerow([
            task.title,
            task.description,
            task.date,
            task.time,
            task.project.name,
            task.duration,
            task.assigned_to.username
        ])

    return response