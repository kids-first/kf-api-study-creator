# Generated by Django 2.1.7 on 2019-05-30 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creator', '0003_add_user_sub'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='picture',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]