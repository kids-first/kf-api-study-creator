# Generated by Django 2.2.13 on 2020-06-23 18:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0019_add_through_relationship'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='role',
            field=models.CharField(choices=[('RESEARCHER', 'Researcher'), ('INVESTIGATOR', 'Investigator'), ('BIOINFO', 'Bioinformatics Staff'), ('ADMIN', 'Administrative Staff'), ('ANALYST', 'Data Analyst Staff'), ('COORDINATOR', 'Coordinating Staff'), ('DEVELOPER', 'Developer')], default='RESEARCHER', help_text='The role of the user in this study', max_length=32),
        ),
    ]
