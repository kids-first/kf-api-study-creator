# Generated by Django 2.2.24 on 2021-11-01 17:53

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0026_update_studies_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='short_code',
            field=models.CharField(default='PLACEHOLDER', max_length=30, validators=[django.core.validators.RegexValidator('^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.'), django.core.validators.MinLengthValidator(3)]),
        ),
    ]
