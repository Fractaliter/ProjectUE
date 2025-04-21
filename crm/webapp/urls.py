from django.urls import path

# Import all views directly from your modularized view files

from webapp.views.base_views import (
    home
)
from webapp.views.auth_views import (
    register, my_login, user_logout
)

from webapp.views.contact_views import (
    contact_dashboard, create_contact, update_contact,
    singular_contact, delete_contact
)

from webapp.views.task_views import (
    task_dashboard, task_list, task_detail, create_task,
    mark_task_complete, mark_task_in_progress, reset_task_to_do
)

from webapp.views.project_views import (
    create_project, manage_projects
)

from webapp.views.user_management_views import (
    manage_users
)

from webapp.views.onboarding_views import (
    onboarding_dashboard, onboarding_setup, update_onboarding_progress,onboarding_projects
)

from webapp.views.statistics_views import (
    statistics_dashboard, export_tasks_csv
)

from webapp.views.spotify_views import (
    artist_search
)

urlpatterns = [
    path('', home, name=""),
    path('register', register, name="register"),
    path('my-login', my_login, name="my-login"),
    path('user-logout', user_logout, name="user-logout"),
    path('manage-users', manage_users, name='manage_users'),

    # CONTACT CRUD
    path('contact_dashboard', contact_dashboard, name="contact_dashboard"),
    path('create_contact', create_contact, name="create_contact"),
    path('update_contact/<int:pk>', update_contact, name='update_contact'),
    path('contact/<int:pk>', singular_contact, name="contact"),
    path('delete_contact/<int:pk>', delete_contact, name="delete_contact"),

    # TASKS
    path('task_dashboard', task_dashboard, name="task_dashboard"),
    path('task_list', task_list, name='task_list'),
    path('task/<int:task_id>/', task_detail, name='task_detail'),
    path('create_task/', create_task, name='create_task'),

    # PROJECTS
    path('create_project/', create_project, name='create_project'),
    path('manage-projects', manage_projects, name='manage_projects'),

    # STATISTICS & EXPORT
    path('statistics_dashboard', statistics_dashboard, name="statistics_dashboard"),
    path('export-csv/', export_tasks_csv, name='export_tasks_csv'),

    # SPOTIFY
    path('artist-search/', artist_search, name='artist_search_url'),

    # ONBOARDING
    path('onboarding/<int:membership_id>/', onboarding_dashboard, name='onboarding_dashboard'),
    path('onboarding/progress/<int:progress_id>/update/', update_onboarding_progress, name='update_onboarding_progress'),
    path('projects/<int:project_id>/onboarding-setup/', onboarding_setup, name='onboarding_setup'),
    path('projects/<int:project_id>/onboarding-setup/', onboarding_setup, name='onboarding_setup'),

    path('tasks/<int:task_id>/complete/', mark_task_complete, name='mark_task_complete'),
    path('tasks/<int:task_id>/in-progress/', mark_task_in_progress, name='mark_task_in_progress'),
    path('tasks/<int:task_id>/reset/', reset_task_to_do, name='reset_task_to_do'),
    path('onboarding_projects', onboarding_projects, name="onboarding_projects")
]
