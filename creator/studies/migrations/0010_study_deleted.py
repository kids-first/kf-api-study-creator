# Generated by Django 2.1.11 on 2019-09-04 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0009_study_grant_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='deleted',
            field=models.BooleanField(default=False, help_text='Whether the study hase been deleted from the dataservice'),
        ),
    ]
