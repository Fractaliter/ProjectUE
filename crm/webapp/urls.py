
from django.urls import path

from . import views

urlpatterns = [

    path('', views.home, name=""),

    path('register', views.register, name="register"),

    path('my-login', views.my_login, name="my-login"),

    path('user-logout', views.user_logout, name="user-logout"),



    # CONTACT  CRUD
    path('contact_dashboard', views.contact_dashboard, name="contact_dashboard"),
    path('create_contact', views.create_contact, name="create_contact"),
    path('update_contact/<int:pk>', views.update_contact, name='update_contact'),
    path('contact/<int:pk>', views.singular_contact, name="contact"),
    path('delete_contact/<int:pk>', views.delete_contact, name="delete_contact"),

    # EVENT  CRUD
    path('event_dashboard', views.event_dashboard, name="event_dashboard"),
    path('event_list', views.event_list, name='event_list'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('create_event/', views.create_event, name='create_event'),
    path('register_event/<int:event_id>/', views.register_event, name='register_event'),

    path('create_project/', views.create_project, name='create_project'),
    
    path('statistics_dashboard', views.statistics_dashboard, name="statistics_dashboard"),
    
    path('artist-search/', views.artist_search, name='artist_search_url'),

    

]






