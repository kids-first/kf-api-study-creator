# Generated by Django 2.2.13 on 2020-09-04 00:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0019_add_file_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='version',
            options={'permissions': [('view_my_version', 'Can view all versions in studies user is a member of'), ('add_my_study_version', 'Can add versions to studies the user is a member of'), ('change_version_meta', 'Can change any version meta'), ('change_version_status', 'Can change any version status'), ('change_my_version_meta', 'Can change version meta in studies the user is a member of'), ('change_my_version_status', 'Can change version status in studies the user is a member of'), ('extract_version_config', 'Can extract any version config'), ('extract_my_version_config', 'Can extract version config in studies the user is a member of')]},
        ),
        migrations.AlterField(
            model_name='file',
            name='file_type',
            field=models.CharField(choices=[('OTH', 'OTH'), ('SEQ', 'SEQ'), ('SHM', 'SHM'), ('CLN', 'CLN'), ('DBG', 'DBG'), ('FAM', 'FAM'), ('S3S', 'S3S')], default='OTH', max_length=3),
        ),
    ]
