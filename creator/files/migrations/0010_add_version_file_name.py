# Generated by Django 2.1.7 on 2019-05-28 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0009_add_version_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='version',
            name='file_name',
            field=models.CharField(default='', help_text="The name of the version's file as it was originally uploaded", max_length=1000),
            preserve_default=False,
        ),
    ]
