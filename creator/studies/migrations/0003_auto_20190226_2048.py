# Generated by Django 2.1.7 on 2019-02-26 20:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0002_auto_20190226_1748'),
    ]

    operations = [
        migrations.AlterField(
            model_name='study',
            name='name',
            field=models.CharField(help_text='The name of the study', max_length=500),
        ),
    ]
