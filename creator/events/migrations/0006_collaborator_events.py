# Generated by Django 2.1.11 on 2020-03-11 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0005_add_buckets'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='event_type',
            field=models.CharField(choices=[('SF_CRE', 'Study File Created'), ('SF_UPD', 'Study File Updated'), ('SF_DEL', 'Study File Deleted'), ('FV_CRE', 'File Version Created'), ('FV_UPD', 'File Version Updated'), ('SD_CRE', 'Study Created'), ('SD_UPD', 'Study Updated'), ('PR_CRE', 'Project Created'), ('PR_UPD', 'Project Updated'), ('PR_DEL', 'Project Deleted'), ('PR_LIN', 'Project Linked'), ('PR_UNL', 'Project Unlinked'), ('PR_STR', 'Project Creation Start'), ('PR_ERR', 'Project Creation Error'), ('PR_SUC', 'Project Creation Success'), ('BK_STR', 'Bucket Creation Start'), ('BK_ERR', 'Bucket Creation Error'), ('BK_SUC', 'Bucket Creation Success'), ('BK_LIN', 'Bucket Linked'), ('BK_UNL', 'Bucket Unlinked'), ('IM_STR', 'File Import Start'), ('IM_ERR', 'File Import Error'), ('IM_SUC', 'File Import Success'), ('CB_ADD', 'Collaborator Added'), ('CB_REM', 'Collaborator Removed'), ('OTH', 'Other')], default='OTH', max_length=6),
        ),
    ]
