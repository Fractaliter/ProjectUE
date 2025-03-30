import csv
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CreateUserForm, LoginForm, CreateContactForm, ContactForm, UpdateContactForm, TaskForm, ProjectForm, CreateRoleForm,AssignProjectRoleForm, AddMemberForm, CreateProjectRoleForm, CreateProjectForm
from django.db.models import Count, Sum
from django.contrib.auth.models import auth
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Contact, Project, ProjectTask, User,UserProfile, UserRole, ProjectRole, ProjectMembership
from django.contrib import messages
from .spotify_utils import get_artist_info
from django.http import HttpResponse


def home(request):
    return render(request, 'webapp/index.html')


def register(request):
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully!")
            return redirect("my-login")
    context = {'form': form}
    return render(request, 'webapp/register.html', context=context)


def my_login(request):
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect("contact_dashboard")
    context = {'form': form}
    return render(request, 'webapp/my-login.html', context=context)


@login_required(login_url='my-login')
def contact_dashboard(request):
    contact_exists = Contact.objects.filter(user=request.user).exists()
    my_contacts = Contact.objects.filter(user=request.user)
    context = {'contacts': my_contacts, 'contact_exists': contact_exists}
    return render(request, 'webapp/contact_dashboard.html', context=context)


@login_required(login_url='my-login')
def task_dashboard(request):
    my_tasks = ProjectTask.objects.filter(assigned_to=request.user)
    my_projects = Project.objects.all()
    context = {'tasks': my_tasks, 'projects': my_projects}
    return render(request, 'webapp/task_dashboard.html', context=context)


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


def user_logout(request):
    auth.logout(request)
    messages.success(request, "Logout success!")
    return redirect("my-login")


def task_list(request):
    tasks = ProjectTask.objects.all()
    return render(request, 'webapp/task_list.html', {'tasks': tasks})


def task_detail(request, task_id):
    task = get_object_or_404(ProjectTask, pk=task_id)
    return render(request, 'webapp/task_detail.html', {'task': task})


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


@login_required
def artist_search(request):
    artist = None
    if request.method == 'POST':
        artist_name = request.POST.get('artist_name')
        artist = get_artist_info(artist_name)
    return render(request, 'webapp/artist_search.html', {'artist': artist})


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
