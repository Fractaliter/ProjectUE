from django.contrib import admin

# Register your models here.

from . models import Record,Event

admin.site.register(Record)
admin.site.register(Event)

