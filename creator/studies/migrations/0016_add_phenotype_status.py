# Generated by Django 2.1.11 on 2020-05-06 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0015_add_ingestion_status'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='study',
            options={'permissions': [('view_my_study', 'Can list studies that the user belongs to'), ('add_collaborator', 'Can add a collaborator to the study'), ('remove_collaborator', 'Can remove a collaborator to the study'), ('change_sequencing_status', 'Can update the sequencing status of a study'), ('change_ingestion_status', 'Can update the ingestion status of a study'), ('change_phenotype_status', 'Can update the phenotype status of a study')]},
        ),
        migrations.AddField(
            model_name='study',
            name='phenotype_status',
            field=models.CharField(choices=[('UNKNOWN', 'Unknown'), ('NOTRECEIVED', 'Not received'), ('INREVIEW', 'In review'), ('APPROVED', 'Approved')], default='UNKNOWN', help_text='Current phenotype status of this study', max_length=16),
        ),
    ]
