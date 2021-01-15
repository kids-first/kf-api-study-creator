# Generated by Django 2.2.13 on 2021-01-15 18:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0003_add_release_log'),
    ]

    operations = [
        migrations.AlterField(
            model_name='release',
            name='job_log',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='releases', to='jobs.JobLog'),
        ),
    ]
