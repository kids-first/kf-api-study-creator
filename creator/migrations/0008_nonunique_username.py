# Generated by Django 2.1.11 on 2019-11-13 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creator', '0007_add_email_notify'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=150, verbose_name='username'),
        ),
    ]