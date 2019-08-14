# Generated by Django 2.1.11 on 2019-08-13 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0008_remove_batch'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='anticipated_samples',
            field=models.PositiveIntegerField(help_text='The expected number of samples for the study', null=True),
        ),
        migrations.AddField(
            model_name='study',
            name='awardee_organization',
            field=models.TextField(default='', help_text='The organization that the grant was awarded to'),
        ),
    ]
