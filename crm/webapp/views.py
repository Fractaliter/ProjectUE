from django.shortcuts import render, redirect, get_object_or_404
from .forms import CreateUserForm, LoginForm, CreateContactForm, UpdateContactForm,EventForm

from django.contrib.auth.models import auth
from django.contrib.auth import authenticate

from django.contrib.auth.decorators import login_required

from .models import Contact,Event, Attendee

from django.contrib import messages



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

    my_contacts = Contact.objects.all()

    context = {'contacts': my_contacts}

    return render(request, 'webapp/contact_dashboard.html', context=context)

# - Event Dashboard

@login_required(login_url='my-login')
def event_dashboard(request):

    my_events = Event.objects.all()

    context = {'events': my_events}

    return render(request, 'webapp/event_dashboard.html', context=context)


# - Create a contact 

@login_required(login_url='my-login')
def create_contact(request):

    form = CreateContactForm()

    if request.method == "POST":

        form = CreateContactForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(request, "Your contact was created!")

            return redirect("dashboard")

    context = {'form': form}

    return render(request, 'webapp/create-contact.html', context=context)


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

    return render(request, 'webapp/update-contact.html', context=context)


# - Read / View a singular contact

@login_required(login_url='my-login')
def singular_contact(request, pk):

    all_contacts = Contact.objects.get(id=pk)

    context = {'contact':all_contacts}

    return render(request, 'webapp/view-contact.html', context=context)


# - Delete a contact

@login_required(login_url='my-login')
def delete_contact(request, pk):

    contact = Contact.objects.get(id=pk)

    contact.delete()

    messages.success(request, "Your contact was deleted!")

    return redirect("dashboard")



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
def register_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    Attendee.objects.get_or_create(user=request.user, event=event)
    return redirect('event_detail', event_id=event.id)



