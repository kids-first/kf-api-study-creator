# Generated by Django 2.1.11 on 2020-04-08 01:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('buckets', '0001_add_buckets'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bucket',
            options={'permissions': [('list_all_bucket', 'Can list all buckets'), ('link_bucket', 'Can link a bucket to a study'), ('unlink_bucket', 'Can unlink a bucket to a study')]},
        ),
    ]
