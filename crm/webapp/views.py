import csv
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CreateUserForm, LoginForm, CreateContactForm,ContactForm, UpdateContactForm,EventForm,ProjectForm
from django.db.models import Count, Sum
from django.contrib.auth.models import auth
from django.contrib.auth import authenticate

from django.contrib.auth.decorators import login_required

from .models import Contact,Event,Attendee,Project,User

from django.contrib import messages

from .spotify_utils import get_artist_info  # Assuming get_artist_info is in spotify_utils.py

from django.http import HttpResponse

# - Homepage 

def home(request):

    return render(request, 'webapp/index.html')


# - Register a user

def register(request):

    form = CreateUserForm()

    if request.method == "POST":

        form = CreateUserForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(request, "Account created successfully!")

            return redirect("my-login")

    context = {'form':form}

    return render(request, 'webapp/register.html', context=context)


# - Login a user

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

    context = {'form':form}

    return render(request, 'webapp/my-login.html', context=context)


# - Contact Dashboard

@login_required(login_url='my-login')
def contact_dashboard(request):
    contact_exists = Contact.objects.filter(user=request.user).exists()
    my_contacts = Contact.objects.filter(user=request.user)

    context = {'contacts': my_contacts,'contact_exists':contact_exists}

    return render(request, 'webapp/contact_dashboard.html', context=context)

# - Event Dashboard

@login_required(login_url='my-login')
def event_dashboard(request):

    my_events = Event.objects.all().filter(organizer_id=request.user.id)

    my_projects = Project.objects.all()

    context = {'events': my_events,'projects':my_projects}

    return render(request, 'webapp/event_dashboard.html', context=context)



# - Create a contact 

@login_required(login_url='my-login')
def create_contact(request):

    if request.method == "POST":
        form = CreateContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)  # Save the form temporarily without committing to the database
            contact.user = request.user  # Assign the logged-in user to the contact
            contact.save()  # Now save the contact to the database
         

            messages.success(request, "Your contact was created!")

            return redirect("contact_dashboard")
    else:
        form = ContactForm()

    return render(request, 'webapp/create_contact.html', {'form': form})

# - Update a contact 

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
        
    context = {'form':form}

    return render(request, 'webapp/update_contact.html', context=context)


# - Read / View a singular contact

@login_required(login_url='my-login')
def singular_contact(request, pk):

    all_contacts = Contact.objects.get(id=pk)

    context = {'contact':all_contacts}

    return render(request, 'webapp/view_contact.html', context=context)


# - Delete a contact

@login_required(login_url='my-login')
def delete_contact(request, pk):

    contact = Contact.objects.get(id=pk)

    contact.delete()

    messages.success(request, "Your contact was deleted!")

    return redirect("contact_dashboard")



# - User logout

def user_logout(request):

    auth.logout(request)

    messages.success(request, "Logout success!")

    return redirect("my-login")

def event_list(request):
    events = Event.objects.all()
    return render(request, 'webapp/event_list.html', {'events': events})

def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    attendees = Attendee.objects.filter(event=event)
    return render(request, 'webapp/event_detail.html', {'event': event, 'attendees': attendees})

@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm()
    return render(request, 'webapp/event_form.html', {'form': form})

@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.save()
            return redirect('event_dashboard')
    else:
        form = ProjectForm()
    return render(request, 'webapp/project_form.html', {'form': form})


@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    Attendee.objects.get_or_create(user=request.user, event=event)
    return redirect('event_detail', event_id=event.id)

def artist_search(request):
    artist = None  # Default to None if no search has been made or if no artist is found
    if request.method == 'POST':
        artist_name = request.POST.get('artist_name')  # Get the artist name from the submitted form data
        artist = get_artist_info(artist_name)  # Use the function to fetch the artist information
        
        # If get_artist_info returns None (artist not found), keep artist as None
        # Otherwise, artist will be the dictionary with the artist's information
    return render(request, 'webapp/artist_search.html', {'artist': artist})

# - Statistics Dashboard
@login_required
def statistics_dashboard(request):
    # Get all projects and organizers for dropdown filters
    projects = Project.objects.all()
    organizers = User.objects.all()

    selected_project = request.GET.get('project')
    selected_organizer = request.GET.get('organizer')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    # Start with all events
    events = Event.objects.all()
    

    # Filter events by selected project if applicable
    if selected_project:
        events = events.filter(project_id=selected_project)

    # Filter events by selected organizer if applicable
    if selected_organizer:
        events = events.filter(organizer_id=selected_organizer)

    # Additional statistics (modify as needed)
    event_count_by_project = Event.objects.values('project__name').annotate(total=Count('id')).order_by('-total')
    event_count_by_organizer = Event.objects.values('organizer__username').annotate(total=Count('id')).order_by('-total')

  # Get the count and total duration of events by project
    event_stats_by_project = Event.objects.values('project__name') \
                                          .annotate(total_events=Count('id'),
                                                    total_duration=Sum('duration')) \
                                          .order_by('-total_events')
    
    # Filtering by date range
    if start_date:
        events = events.filter(date__gte=start_date)
    if end_date:
        events = events.filter(date__lte=end_date)
        
    total_duration = events.aggregate(Sum('duration'))['duration__sum'] or 0
    context = {
        'projects': projects,
        'organizers': organizers,
        'events': events,
        'event_count_by_project': event_count_by_project,
        'event_count_by_organizer': event_count_by_organizer,
        'event_stats_by_project': event_stats_by_project,
        'selected_project': selected_project,
        'selected_organizer': selected_organizer,
        'start_date': start_date,
        'end_date': end_date,
        'total_duration': total_duration  # Total duration of filtered events
    }

    return render(request, 'webapp/statistics_dashboard.html', context)

def export_events_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="filtered_tasks.csv"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Description', 'Date', 'Time', 'Project', 'Duration', 'Organizer'])

    events = Event.objects.all()

    if request.GET.get('project'):
        events = events.filter(project_id=request.GET['project'])

    if request.GET.get('organizer'):
        events = events.filter(organizer_id=request.GET['organizer'])

    if request.GET.get('start_date'):
        events = events.filter(date__gte=request.GET['start_date'])

    if request.GET.get('end_date'):
        events = events.filter(date__lte=request.GET['end_date'])

    for event in events:
        writer.writerow([
            event.title,
            event.description,
            event.date,
            event.time,
            event.project.name,
            event.duration,
            event.organizer.username
        ])

    return response