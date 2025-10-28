# Generated migration for AI status fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0008_llm_assisted_onboarding'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentsource',
            name='ai_generation_status',
            field=models.CharField(
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
            ),
        ),
        migrations.AddField(
            model_name='documentsource',
            name='ai_processing_started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='documentsource',
            name='ai_processing_completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='documentsource',
            name='ai_processing_error',
            field=models.TextField(
                blank=True,
                help_text='Error message if processing failed',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='documentsource',
            name='ai_processing_progress',
            field=models.IntegerField(
                default=0,
                help_text='Processing progress percentage (0-100)',
            ),
        ),
    ]

