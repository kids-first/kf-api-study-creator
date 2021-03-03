# Generated by Django 2.2.13 on 2021-02-23 19:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_reviews', '0001_initial'),
        ('events', '0013_updated_event_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='data_review',
            field=models.ForeignKey(blank=True, help_text='Data Review related to this event', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', to='data_reviews.DataReview'),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_type',
            field=models.CharField(choices=[('SF_CRE', 'Study File Created'), ('SF_UPD', 'Study File Updated'), ('SF_DEL', 'Study File Deleted'), ('FV_CRE', 'File Version Created'), ('FV_UPD', 'File Version Updated'), ('SD_CRE', 'Study Created'), ('SD_UPD', 'Study Updated'), ('PR_CRE', 'Project Created'), ('PR_UPD', 'Project Updated'), ('PR_DEL', 'Project Deleted'), ('PR_LIN', 'Project Linked'), ('PR_UNL', 'Project Unlinked'), ('PR_STR', 'Project Creation Start'), ('PR_ERR', 'Project Creation Error'), ('PR_SUC', 'Project Creation Success'), ('BK_STR', 'Bucket Creation Start'), ('BK_ERR', 'Bucket Creation Error'), ('BK_SUC', 'Bucket Creation Success'), ('BK_LIN', 'Bucket Linked'), ('BK_UNL', 'Bucket Unlinked'), ('IM_STR', 'File Import Start'), ('IM_ERR', 'File Import Error'), ('IM_SUC', 'File Import Success'), ('CB_ADD', 'Collaborator Added'), ('CB_UPD', 'Collaborator Updated'), ('CB_REM', 'Collaborator Removed'), ('IN_UPD', 'Ingestion Status Updated'), ('PH_UPD', 'Phenotype Status Updated'), ('ST_UPD', 'Sequencing Status Updated'), ('RT_CRE', 'Referral Token Created'), ('RT_CLA', 'Referral Token Claimed'), ('SL_STR', 'Slack Channel Creation Start'), ('SL_ERR', 'Slack Channel Creation Error'), ('SL_SUC', 'Slack Channel Creation Success'), ('DR_STA', 'Data Review Started'), ('DR_WAI', 'Data Review Waiting for Updates'), ('DR_UPD', 'Data Review Updated'), ('DR_APP', 'Data Review Approved'), ('DR_CLO', 'Data Review Closed'), ('DR_REO', 'Data Review Re-opened'), ('OTH', 'Other')], default='OTH', max_length=6),
        ),
    ]