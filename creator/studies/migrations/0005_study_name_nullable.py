# Generated by Django 2.1.7 on 2019-08-02 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0004_update_short_name_limit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='study',
            name='name',
            field=models.CharField(help_text='The name of the study', max_length=500, null=True),
        ),
    ]