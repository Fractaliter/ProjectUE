from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from webapp.models import UserProfile, ProjectMembership, OnboardingTaskTemplate, OnboardingTask, OnboardingStep, Project

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=Project)
def make_creator_admin(sender, instance, created, **kwargs):
    """Automatically make project creator an admin"""
    if created and instance.creator:
        # Check if membership already exists
        membership, created = ProjectMembership.objects.get_or_create(
            user=instance.creator,
            project=instance,
            defaults={'is_admin': True}
        )
        if not created and not membership.is_admin:
            # Update existing membership to make creator admin
            membership.is_admin = True
            membership.save()
        
@receiver(post_save, sender=ProjectMembership)
def create_onboarding_tasks_for_new_member(sender, instance, created, **kwargs):
    if created and instance.role:
        step_templates = OnboardingTaskTemplate.objects.filter(step__role=instance.role)
        for template in step_templates:
            # Zabezpieczenie przed duplikatami
            exists = OnboardingTask.objects.filter(
                membership=instance,
                template=template
            ).exists()
            if not exists:
                OnboardingTask.objects.create(
                    title=template.title,
                    description=template.description,
                    assigned_to=instance.user,
                    membership=instance,
                    template=template,
                )