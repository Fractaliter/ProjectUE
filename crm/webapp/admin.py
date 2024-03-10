from django.contrib import admin

# Register your models here.

from . models import Contact,Event

admin.site.register(Contact)
admin.site.register(Event)

