from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils import timezone
from django.contrib.postgres.fields import JSONField


# From https://stackoverflow.com/questions/50480924/regex-for-s3-bucket-name
BUCKET_RE = (
    r"(?=^.{3,63}$)(?!^(\d+\.)+\d+$)(^(([a-z0-9]|[a-z0-9][a-z0-9\-]*"
    r"[a-z0-9])\.)*([a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])$)"
)

SEQ_STATUS_CHOICES = [
    ("UNKNOWN", "Unknown"),
    ("NOTSTART", "Not Started"),
    ("INPROG", "In Progress"),
    ("COMPLETE", "Complete"),
]
ING_STATUS_CHOICES = [
    ("UNKNOWN", "Unknown"),
    ("NOTSTART", "Not Started"),
    ("INPROG", "In Progress"),
    ("COMPLETE", "Complete"),
]
PHE_STATUS_CHOICES = [
    ("UNKNOWN", "Unknown"),
    ("NOTRECEIVED", "Not received"),
    ("INREVIEW", "In review"),
    ("APPROVED", "Approved"),
]
MEMBER_ROLE_CHOICES = [
    ("RESEARCHER", "Researcher"),
    ("INVESTIGATOR", "Investigator"),
    ("BIOINFO", "Bioinformatics Staff"),
    ("ADMIN", "Administrative Staff"),
    ("ANALYST", "Data Analyst Staff"),
    ("COORDINATOR", "Coordinating Staff"),
    ("DEVELOPER", "Developer"),
]
DOMAIN_CHOICES = [
    ("UNKNOWN", "Unknown"),
    ("CANCER", "Cancer"),
    ("BIRTHDEFECT", "Birth Defect"),
    ("CANCERANDBIRTHDEFECT", "Cancer and Birth Defect"),
    ("COVID19", "COVID-19"),
    ("OTHER", "Other"),
]

ALPHANUMERIC = RegexValidator(
    r"^[0-9a-zA-Z]*$",
    "Only alphanumeric characters are allowed.",
)


class Study(models.Model):
    """
    A study encompasses a group of participants subjected to similar analysis.
    """

    class Meta:
        permissions = [
            ("view_my_study", "Can list studies that the user belongs to"),
            ("add_collaborator", "Can add a collaborator to the study"),
            ("remove_collaborator", "Can remove a collaborator to the study"),
            (
                "change_sequencing_status",
                "Can update the sequencing status of a study",
            ),
            (
                "change_ingestion_status",
                "Can update the ingestion status of a study",
            ),
            (
                "change_phenotype_status",
                "Can update the phenotype status of a study",
            ),
            (
                "subscribe_study",
                "Can subscribe to a study for notifications",
            ),
            (
                "subscribe_my_study",
                "Can subscribe to a study that the user belongs to.",
            ),
            (
                "unsubscribe_study",
                "Can unsubscribe to a study for notifications",
            ),
            (
                "unsubscribe_my_study",
                "Can unsubscribe to a study that the user belongs to.",
            ),
        ]

    kf_id = models.CharField(
        max_length=11,
        primary_key=True,
        help_text="The Kids First Identifier",
        null=False,
    )
    dewrangle_id = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        help_text="Unique identifier of the study in Dewrangle"
    )
    name = models.CharField(
        max_length=500, help_text="The name of the study", null=True
    )
    visible = models.BooleanField(
        default=True, help_text="If the study is public or not"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, null=True, help_text="Time the study was created"
    )
    bucket = models.CharField(
        max_length=63,
        validators=[RegexValidator(BUCKET_RE)],
        help_text="The s3 bucket name",
    )
    investigator_name = models.CharField(
        max_length=200,
        help_text="The name of the principle investigator of the study",
        null=True,
    )
    slack_channel = models.CharField(
        max_length=80,
        help_text="The name of the related Slack channel",
        null=True,
    )
    modified_at = models.DateTimeField(
        auto_now=True, null=False, help_text="Time of last modification"
    )
    attribution = models.CharField(
        max_length=100,
        null=True,
        help_text=("Link to attribution prose" " provided by dbGaP"),
    )
    data_access_authority = models.CharField(max_length=30, null=True)
    external_id = models.CharField(
        max_length=30, null=False, help_text="dbGaP accession number"
    )
    release_status = models.CharField(
        max_length=30, null=True, help_text="Release status of the study"
    )
    short_name = models.CharField(
        max_length=500, null=True, help_text="Short name for study"
    )
    version = models.CharField(
        max_length=10, null=True, help_text="dbGaP version"
    )
    release_date = models.DateField(
        null=True, help_text="Scheduled date for release of the study"
    )
    description = models.TextField(
        null=False, default="", help_text="Markdown description of the study"
    )
    anticipated_samples = models.PositiveIntegerField(
        null=True, help_text="The expected number of samples for the study"
    )
    awardee_organization = models.TextField(
        null=False,
        default="",
        help_text="The organization that the grant was awarded to",
    )
    deleted = models.BooleanField(
        default=False,
        help_text="Whether the study hase been deleted from the dataservice",
    )
    additional_fields = JSONField(default=dict)
    short_code = models.CharField(
        max_length=30,
        validators=[ALPHANUMERIC, MinLengthValidator(3)],
        default="PLACEHOLDER",
    )
    domain = models.CharField(
        max_length=20,
        default="UNKNOWN",
        choices=DOMAIN_CHOICES,
        help_text="Category of disease being studied",
        blank=True,
    )
    program = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="The administrative organization or group of the Study",
    )
    # Status fields
    sequencing_status = models.CharField(
        max_length=16,
        default="UNKNOWN",
        choices=SEQ_STATUS_CHOICES,
        help_text="Current sequencing status of this study",
    )
    ingestion_status = models.CharField(
        max_length=16,
        default="UNKNOWN",
        choices=ING_STATUS_CHOICES,
        help_text="Current ingestion status of this study",
    )
    phenotype_status = models.CharField(
        max_length=16,
        default="UNKNOWN",
        choices=PHE_STATUS_CHOICES,
        help_text="Current phenotype status of this study",
    )

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="studies",
    )

    collaborators = models.ManyToManyField(
        "creator.User",
        related_name="studies",
        help_text="Users working on this study",
        through="Membership",
        through_fields=("study", "collaborator"),
    )

    slack_notify = models.BooleanField(
        default=True,
        help_text="Whether enabled slack notifications for study updates",
    )

    def __str__(self):
        return self.kf_id


class Membership(models.Model):
    """
    Describes the nature of a collaborator's inclusion in a study.
    """

    class Meta:
        unique_together = ["collaborator", "study"]

    collaborator = models.ForeignKey("creator.User", on_delete=models.CASCADE)
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    invited_by = models.ForeignKey(
        "creator.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="invited_by",
        help_text="The user that invited this collaborator to the study",
    )
    joined_on = models.DateTimeField(
        auto_now_add=True,
        null=False,
        help_text="Time when user joined the study",
    )
    role = models.CharField(
        max_length=32,
        default="RESEARCHER",
        choices=MEMBER_ROLE_CHOICES,
        help_text="The role of the user in this study",
    )
