from django.contrib import admin

# Register your models here.

from webapp.models import Contact,ProjectTask,Project,UserRole,UserProfile,OnboardingTaskTemplate,OnboardingTask

admin.site.register(Contact)
admin.site.register(ProjectTask)
admin.site.register(Project)
admin.site.register(UserRole)
admin.site.register(UserProfile)
admin.site.register(OnboardingTaskTemplate)
admin.site.register(OnboardingTask)

