# Generated by Django 2.1.7 on 2019-05-28 14:14

from django.db import migrations


def combine_names(apps, schema_editor):
    """
    We will populate any existing versions with the name of the parent file
    """
    Version = apps.get_model('files', 'Version')
    for version in Version.objects.all():
        version.file_name = version.root_file.name
        version.save()


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0010_add_version_file_name'),
    ]

    operations = [
        migrations.RunPython(combine_names),
    ]
