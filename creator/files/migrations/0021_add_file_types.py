# Generated by Django 2.2.13 on 2020-09-16 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0020_version_extract_config_permission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='file_type',
            field=models.CharField(choices=[('OTH', 'OTH'), ('SEQ', 'SEQ'), ('SHM', 'SHM'), ('CLN', 'CLN'), ('DBG', 'DBG'), ('FAM', 'FAM'), ('S3S', 'S3S'), ('PDA', 'PDA'), ('FTR', 'FTR')], default='OTH', max_length=3),
        ),
    ]