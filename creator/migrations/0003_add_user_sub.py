# Generated by Django 2.1.7 on 2019-05-30 00:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creator', '0002_auto_20190321_1936'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='sub',
            field=models.CharField(db_index=True, default='', help_text='The subject of the JWT and primary user identifier', max_length=150, unique=True),
            preserve_default=False,
        ),
    ]
