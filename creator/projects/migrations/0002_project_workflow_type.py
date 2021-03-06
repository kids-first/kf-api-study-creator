# Generated by Django 2.1.11 on 2019-08-08 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_add_projects'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='workflow_type',
            field=models.CharField(choices=[('bwa-mem', 'bwa-mem'), ('bwa-mem-bqsr', 'bwa-mem-bqsr'), ('star-2-pass', 'star-2-pass'), ('gatk-haplotypecaller', 'gatk-haplotypecaller'), ('gatk-genotypgvcf', 'gatk-genotypgvcf'), ('gatk-genotypgvcf-vqsr', 'gatk-genotypgvcf-vqsr'), ('strelka2-somatic-mode', 'strelka2-somatic-mode'), ('mutect2-somatic-mode', 'mutect2-somatic-mode'), ('mutect2-tumor-only-mode', 'mutect2-tumor-only-mode'), ('vardict-single-sample-mode', 'vardict-single-sample-mode'), ('vardict-paired-sample-mode', 'vardict-paired-sample-mode'), ('control-freec-somatic-mode', 'control-freec-somatic-mode'), ('control-freec-germline-mode', 'control-freec-germline-mode'), ('stringtie-expression', 'stringtie-expression'), ('manta-somatic', 'manta-somatic'), ('manta-germline', 'manta-germline'), ('lumpy-somatic', 'lumpy-somatic'), ('lumpy-germline', 'lumpy-germline'), ('rsem', 'rsem'), ('kallisto', 'kallisto'), ('star-fusion', 'star-fusion'), ('arriba', 'arriba'), ('peddy', 'peddy')], help_text='The Cavatica project workflow type', max_length=200, null=True),
        ),
    ]
