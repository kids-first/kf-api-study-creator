# Generated by Django 2.1.7 on 2019-02-26 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='attribution',
            field=models.CharField(help_text='Link to attribution prose provided by dbGaP', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='study',
            name='data_access_authority',
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='study',
            name='external_id',
            field=models.CharField(default='test', help_text='dbGaP accession number', max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='study',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, help_text='Time of last modification'),
        ),
        migrations.AddField(
            model_name='study',
            name='release_status',
            field=models.CharField(help_text='Release status of the study', max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='study',
            name='short_name',
            field=models.CharField(help_text='Short name for study', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='study',
            name='version',
            field=models.CharField(help_text='dbGaP version', max_length=10, null=True),
        ),
    ]
