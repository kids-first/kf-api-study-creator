# Generated by Django 2.1.11 on 2019-09-04 13:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_project_deleted_field'),
        ('events', '0002_correct_enums'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='project',
            field=models.ForeignKey(blank=True, help_text='Project related to this event', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', to='projects.Project'),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_type',
            field=models.CharField(choices=[('SF_CRE', 'Study File Created'), ('SF_UPD', 'Study File Updated'), ('SF_DEL', 'Study File Deleted'), ('FV_CRE', 'File Version Created'), ('FV_UPD', 'File Version Updated'), ('SD_CRE', 'Study Created'), ('SD_UPD', 'Study Updated'), ('PR_CRE', 'Project Created'), ('PR_UPD', 'Project Updated'), ('PR_DEL', 'Project Deleted'), ('PR_LIN', 'Project Linked'), ('PR_UNL', 'Project Unlinked'), ('OTH', 'Other')], default='OTH', max_length=6),
        ),
    ]
