# Generated by Django 2.1.7 on 2019-06-12 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0003_auto_20190226_2048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='study',
            name='short_name',
            field=models.CharField(help_text='Short name for study', max_length=500, null=True),
        ),
    ]