# Generated by Django 2.1.7 on 2019-03-27 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0002_downloadtoken'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='file_type',
            field=models.CharField(choices=[('OTH', 'Other'), ('SEQ', 'Sequencing Manifest'), ('SHM', 'Shipping Manifest'), ('CLN', 'Clinical Data'), ('FAM', 'Familial Relationships')], default='OTH', max_length=3),
        ),
    ]
