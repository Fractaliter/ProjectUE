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
def artist_search(request):
    artist = None
    if request.method == 'POST':
        artist_name = request.POST.get('artist_name')
        artist = get_artist_info(artist_name)
    return render(request, 'webapp/artist_search.html', {'artist': artist})