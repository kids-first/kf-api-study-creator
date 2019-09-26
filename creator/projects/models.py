from django.db import models
from creator.studies.models import Study

WORKFLOW_TYPES = (
    ("bwa_mem", "bwa-mem"),
    ("bwa_mem_bqsr", "bwa-mem-bqsr"),
    ("star_2_pass", "star-2-pass"),
    ("gatk_haplotypecaller", "gatk-haplotypecaller"),
    ("gatk_genotypgvcf", "gatk-genotypgvcf"),
    ("gatk_genotypgvcf_vqsr", "gatk-genotypgvcf-vqsr"),
    ("strelka2_somatic_mode", "strelka2-somatic-mode"),
    ("mutect2_somatic_mode", "mutect2-somatic-mode"),
    ("mutect2_tumor_only_mode", "mutect2-tumor-only-mode"),
    ("vardict_single_sample_mode", "vardict-single-sample-mode"),
    ("vardict_paired_sample_mode", "vardict-paired-sample-mode"),
    ("control_freec_somatic_mode", "control-freec-somatic-mode"),
    ("control_freec_germline_mode", "control-freec-germline-mode"),
    ("stringtie_expression", "stringtie-expression"),
    ("manta_somatic", "manta-somatic"),
    ("manta_germline", "manta-germline"),
    ("lumpy_somatic", "lumpy-somatic"),
    ("lumpy_germline", "lumpy-germline"),
    ("rsem", "rsem"),
    ("kallisto", "kallisto"),
    ("star_fusion", "star-fusion"),
    ("arriba", "arriba"),
    ("peddy", "peddy"),
)

PROJECT_TYPES = (
    ("HAR", "harmonization"),
    ("DEL", "delivery"),
    ("RES", "research"),
)


class Project(models.Model):
    """
    Represents a project created in Cavatica.
    Documentation: http://docs.cavatica.org/docs/projects
    """

    project_id = models.CharField(
        primary_key=True,
        max_length=200,
        null=False,
        help_text="The Cavatica project identifier",
    )
    name = models.CharField(
        max_length=500,
        null=False,
        help_text="The name of the Cavatica project",
    )
    description = models.TextField(
        null=False,
        help_text="The description markdown of the Cavatica project",
    )
    url = models.CharField(
        max_length=500, null=False, help_text="The url of the Cavatica project"
    )
    project_type = models.CharField(
        choices=PROJECT_TYPES,
        max_length=3,
        default="HAR",
        help_text="The Cavatica project type",
    )
    workflow_type = models.CharField(
        max_length=200,
        choices=WORKFLOW_TYPES,
        null=True,
        help_text="The Cavatica project workflow type",
    )
    created_by = models.CharField(
        max_length=200,
        null=False,
        help_text="The user who created the Cavatica project",
    )
    created_on = models.DateTimeField(
        null=False, help_text="Time the Cavatica project was created"
    )
    modified_on = models.DateTimeField(
        null=False, help_text="Time of last modification"
    )
    study = models.ForeignKey(
        Study,
        related_name="projects",
        help_text="The study this project belongs to",
        on_delete=models.SET_NULL,
        null=True,
    )
    deleted = models.BooleanField(
        null=False,
        default=False,
        help_text="Whether this project has been deleted from Cavatica",
    )

    def __str__(self):
        return self.project_id
