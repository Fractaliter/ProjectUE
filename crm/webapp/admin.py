from django.contrib import admin

# Register your models here.

from . models import Contact,Task,Project

admin.site.register(Contact)
admin.site.register(Task)
admin.site.register(Project)

