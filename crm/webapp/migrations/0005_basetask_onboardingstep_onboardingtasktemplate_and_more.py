# Generated by Django 4.2 on 2025-03-30 12:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('webapp', '0004_rename_event_task'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('todo', 'To Do'), ('in_progress', 'In progress'), ('completed', 'Completed')], default='todo', max_length=20)),
                ('assigned_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='base_tasks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OnboardingStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='OnboardingTaskTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('is_required', models.BooleanField(default=True)),
                ('step', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_templates', to='webapp.onboardingstep')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProjectRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='task',
            name='organizer',
        ),
        migrations.RemoveField(
            model_name='task',
            name='project',
        ),
        migrations.AddField(
            model_name='project',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='creator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='OnboardingTask',
            fields=[
                ('basetask_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='webapp.basetask')),
                ('completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('added_by_user', models.BooleanField(default=False)),
            ],
            bases=('webapp.basetask',),
        ),
        migrations.CreateModel(
            name='ProjectTask',
            fields=[
                ('basetask_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='webapp.basetask')),
                ('date', models.DateField()),
                ('time', models.TimeField()),
                ('duration', models.IntegerField(default=1)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='webapp.project')),
            ],
            bases=('webapp.basetask',),
        ),
        migrations.DeleteModel(
            name='Attendee',
        ),
        migrations.DeleteModel(
            name='Task',
        ),
        migrations.AddField(
            model_name='projectrole',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roles', to='webapp.project'),
        ),
        migrations.AddField(
            model_name='projectmembership',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='webapp.project'),
        ),
        migrations.AddField(
            model_name='projectmembership',
            name='role',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='webapp.projectrole'),
        ),
        migrations.AddField(
            model_name='projectmembership',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='onboardingstep',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='webapp.projectrole'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='role',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='webapp.userrole'),
        ),
        migrations.AlterUniqueTogether(
            name='projectrole',
            unique_together={('project', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='projectmembership',
            unique_together={('user', 'project')},
        ),
        migrations.AddField(
            model_name='onboardingtask',
            name='membership',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_onboarding_tasks', to='webapp.projectmembership'),
        ),
        migrations.AddField(
            model_name='onboardingtask',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='webapp.onboardingtasktemplate'),
        ),
        migrations.AlterUniqueTogether(
            name='onboardingtask',
            unique_together={('template', 'membership')},
        ),
    ]
