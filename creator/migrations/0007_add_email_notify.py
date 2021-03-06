# Generated by Django 2.1.11 on 2019-10-22 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creator', '0006_add_slack_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_notify',
            field=models.BooleanField(default=False, help_text='Whether the user has enabled email notifications'),
        ),
    ]
