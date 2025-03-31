
from django.urls import path

from . import views

urlpatterns = [

    path('', views.home, name=""),

    path('register', views.register, name="register"),

    path('my-login', views.my_login, name="my-login"),

    path('user-logout', views.user_logout, name="user-logout"),
    path('manage-users', views.manage_users, name='manage_users'),



    # CONTACT  CRUD
    path('contact_dashboard', views.contact_dashboard, name="contact_dashboard"),
    path('create_contact', views.create_contact, name="create_contact"),
    path('update_contact/<int:pk>', views.update_contact, name='update_contact'),
    path('contact/<int:pk>', views.singular_contact, name="contact"),
    path('delete_contact/<int:pk>', views.delete_contact, name="delete_contact"),

    # EVENT  CRUD
    path('task_dashboard', views.task_dashboard, name="task_dashboard"),
    path('task_list', views.task_list, name='task_list'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('create_task/', views.create_task, name='create_task'),

    path('create_project/', views.create_project, name='create_project'),
    
    path('statistics_dashboard', views.statistics_dashboard, name="statistics_dashboard"),
    
    path('artist-search/', views.artist_search, name='artist_search_url'),
    path('export-csv/', views.export_tasks_csv, name='export_tasks_csv'),
    path('manage-projects', views.manage_projects, name='manage_projects'), 
    path('onboarding/<int:membership_id>/', views.onboarding_dashboard, name='onboarding_dashboard'),
    path('onboarding/progress/<int:progress_id>/update/', views.update_onboarding_progress, name='update_onboarding_progress'),
    path('projects/<int:project_id>/onboarding-setup/', views.onboarding_setup, name='onboarding_setup'),

    path('tasks/<int:task_id>/complete/', views.mark_task_complete, name='mark_task_complete'),
    path('tasks/<int:task_id>/in-progress/', views.mark_task_in_progress, name='mark_task_in_progress'),
    path('tasks/<int:task_id>/reset/', views.reset_task_to_do, name='reset_task_to_do'),
    

]






