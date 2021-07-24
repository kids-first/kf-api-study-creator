# Generated by Django 2.2.21 on 2021-06-22 14:45

import creator.data_templates.models
from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DataTemplate',
            fields=[
                ('id', models.CharField(default=creator.data_templates.models.template_id,
                 help_text='Human friendly ID assigned to the data template', max_length=11, primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4,
                 help_text='UUID used internally')),
                ('created_at', models.DateTimeField(auto_now_add=True,
                 help_text='Time when the data template was created', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True,
                 help_text='Time when the data template was modified', null=True)),
                ('name', models.CharField(
                    help_text='Name of the data template', max_length=256)),
                ('description', models.TextField(
                    help_text='Description of data template', max_length=10000)),
                ('icon', models.CharField(
                    blank=True, help_text='Name of the Font Awesome icon to use when displaying the template in the frontend web application', max_length=256, null=True)),
                ('creator', models.ForeignKey(blank=True, help_text='The user who created the data template', null=True,
                 on_delete=django.db.models.deletion.SET_NULL, related_name='data_templates', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(help_text='The organization that owns the data template',
                 on_delete=django.db.models.deletion.CASCADE, related_name='data_templates', to='organizations.Organization')),
            ],
            options={
                'permissions': [('list_all_datatemplate', 'Show all data_template')],
            },
        ),
        migrations.CreateModel(
            name='TemplateVersion',
            fields=[
                ('id',
                 models.CharField(default=creator.data_templates.models.template_version_id,
                                  help_text='Human friendly ID assigned to the template version', max_length=11, primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4,
                 help_text='UUID used internally')),
                ('created_at', models.DateTimeField(auto_now_add=True,
                 help_text='Time when the template version was created', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True,
                 help_text='Time when the template version was modified', null=True)),
                ('description', models.TextField(
                    help_text='Description of changes in this template version', max_length=10000)),
                ('field_definitions', django.contrib.postgres.fields.jsonb.JSONField(
                    default=dict, help_text='The field definitions for this template version')),
                ('creator', models.ForeignKey(blank=True, help_text='The user who created the template version', null=True,
                 on_delete=django.db.models.deletion.SET_NULL, related_name='template_versions', to=settings.AUTH_USER_MODEL)),
                ('data_template', models.ForeignKey(help_text='The data template this template version belongs to',
                 on_delete=django.db.models.deletion.CASCADE, related_name='template_versions', to='data_templates.DataTemplate')),
                ('studies', models.ManyToManyField(help_text='The studies this template version is assigned to',
                 related_name='template_versions', to='studies.Study')),
            ],
            options={
                'permissions': [('list_all_templateversion', 'Show all template_version')],
            },
        ),
    ]