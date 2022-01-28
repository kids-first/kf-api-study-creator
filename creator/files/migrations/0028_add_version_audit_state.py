# Generated by Django 2.2.24 on 2021-12-10 01:39

from django.db import migrations
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0027_restore_old_file_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='version',
            name='audit_prep_state',
            field=django_fsm.FSMField(default='not_applicable', help_text='The state of the version in the preparation for audit submission', max_length=50),
        ),
    ]