# Generated by Django 2.1.7 on 2019-02-25 16:35

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('studies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(help_text='Description of the file', max_length=1000)),
                ('file_type', models.CharField(choices=[('SAM', 'Sample Manifest'), ('SHM', 'Shipping Manifest'), ('CLN', 'Clinical Data'), ('FAM', 'Familial Relationships')], max_length=3)),
                ('study', models.ForeignKey(help_text='The study this file belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='files', to='studies.Study')),
            ],
        ),
        migrations.CreateModel(
            name='Object',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.FileField(help_text='Field to track the storage location of the object', upload_to='uploads/')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, help_text='Time the object was created')),
                ('size', models.BigIntegerField(help_text='Size of the object in bytes', validators=[django.core.validators.MinValueValidator(0, 'File size must be a positive number')])),
                ('root_file', models.ForeignKey(help_text='The file that this version object belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='files.File')),
            ],
        ),
    ]
