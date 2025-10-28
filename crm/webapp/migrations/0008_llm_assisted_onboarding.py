# Generated migration for LLM-assisted onboarding

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('webapp', '0007_projectmembership_is_admin_and_more'),
    ]

    operations = [
        # Rozszerzenie OnboardingTaskTemplate o nowe pola LLM
        migrations.AddField(
            model_name='onboardingtasktemplate',
            name='acceptance_criteria',
            field=models.TextField(blank=True, help_text='Kryteria akceptacji (bullet list)', null=True),
        ),
        migrations.AddField(
            model_name='onboardingtasktemplate',
            name='estimated_time_hours',
            field=models.FloatField(blank=True, help_text='Szacowany czas w godzinach', null=True),
        ),
        migrations.AddField(
            model_name='onboardingtasktemplate',
            name='source_context_ids',
            field=models.JSONField(blank=True, help_text='IDs fragmentów z RAG/dokumentacji', null=True),
        ),
        migrations.AddField(
            model_name='onboardingtasktemplate',
            name='depends_on',
            field=models.JSONField(blank=True, help_text='Lista ID zadań, od których zależy ten task', null=True),
        ),
        
        # Nowy model: OnboardingTemplateVersion
        migrations.CreateModel(
            name='OnboardingTemplateVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.IntegerField(default=1)),
                ('llm_model', models.CharField(help_text='Nazwa użytego modelu LLM', max_length=100)),
                ('prompt_hash', models.CharField(help_text='Hash promptu dla audytu', max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('changelog', models.TextField(help_text='Opis zmian w wersji')),
                ('draft_data', models.JSONField(blank=True, help_text='Draft JSON przed zatwierdzeniem', null=True)),
                ('is_active', models.BooleanField(default=False, help_text='Czy wersja jest aktywna')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('step', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='webapp.onboardingstep')),
            ],
            options={
                'ordering': ['-version'],
                'unique_together': {('step', 'version')},
            },
        ),
        
        # Nowy model: DocumentSource
        migrations.CreateModel(
            name='DocumentSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('file', models.FileField(blank=True, null=True, upload_to='onboarding_docs/')),
                ('content', models.TextField(help_text='Ekstraktowana treść dokumentu')),
                ('doc_type', models.CharField(choices=[('pdf', 'PDF'), ('md', 'Markdown'), ('html', 'HTML'), ('txt', 'Text')], max_length=20)),
                ('url', models.URLField(blank=True, help_text='Link do dokumentu zewnętrznego', null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ai_generation_status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('processing', 'Processing'),
                        ('completed', 'Completed'),
                        ('failed', 'Failed'),
                        ('skipped', 'Skipped'),
                    ],
                    default='pending',
                    help_text='Status of AI processing for this document',
                    max_length=20,
                )),
                ('ai_processing_started_at', models.DateTimeField(blank=True, null=True)),
                ('ai_processing_completed_at', models.DateTimeField(blank=True, null=True)),
                ('ai_processing_error', models.TextField(
                    blank=True,
                    help_text='Error message if processing failed',
                    null=True,
                )),
                ('ai_processing_progress', models.IntegerField(
                    default=0,
                    help_text='Processing progress percentage (0-100)',
                )),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='webapp.project')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]


