import os
import uuid
import secrets
from enum import Enum
from functools import partial
from datetime import datetime
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from creator.studies.models import Study
from creator.fields import KFIDField, kf_id_generator
from creator.analyses.file_types import FILE_TYPES

User = get_user_model()


def file_id():
    return kf_id_generator("SF")


def only_printable(string):
    """ Converts to a string and removes any non-printable characters"""
    string = str(string)
    return "".join([s for s in string if s.isprintable()])


class FileType(Enum):
    OTH = "OTH"  # Other
    SHM = "SHM"  # OLD: Sequencing Harmonizition Manifest
    CLN = "CLN"  # OLD: Clinical File
    DBG = "DBG"  # OLD: dbGaP Submission file
    FAM = "FAM"  # OLD: Family Relationship
    S3S = "S3S"  # S3 Scrape
    PDA = "PDA"  # Participant Details
    PTD = "PTD"  # Participant Diseases
    PTP = "PTP"  # Participant Phenotypes
    GOB = "GOB"  # General Observations
    FTR = "FTR"  # Family Trio
    FCM = "FCM"  # Complex Family
    GWO = "GWO"  # Genomic Workflow Output Manifest
    BCM = "BCM"  # Biospecimen Collection Manifest
    BBM = "BBM"  # Biobank Manifest
    ALM = "ALM"  # Aliquot Manifest
    SEQ = "SEQ"  # Sequencing File Manifest


class File(models.Model):
    """
    The 'essence' of a file. Describes the ideal data, which underlying
    content may be iterated on as new 'versions'.
    """

    class Meta:
        permissions = [
            ("list_all_file", "Can list all files"),
            (
                "view_my_file",
                "Can view all files in studies user is a member of",
            ),
            (
                "add_my_study_file",
                "Can add files to studies the user is a member of",
            ),
            (
                "change_my_study_file",
                "Can change files in studies the user is a member of",
            ),
        ]

    kf_id = KFIDField(primary_key=True, default=file_id)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(
        max_length=10000, help_text="Description of the file"
    )
    study = models.ForeignKey(
        Study,
        related_name="files",
        help_text="The study this file belongs to",
        on_delete=models.CASCADE,
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="files",
        help_text="The user who originally created this File",
    )

    file_type = models.CharField(
        max_length=3,
        choices=[(t.name, t.value) for t in FileType],
        default="OTH",
    )

    tags = ArrayField(
        models.CharField(max_length=50, blank=True),
        blank=True,
        default=list,
        help_text="Tags to group the files by",
    )

    def clean(self):
        if (
            self.study is None
            and self.versions.latest("created_at").study is None
        ):
            raise ValidationError(
                "Study must be specified or the version given must have a "
                "linked study"
            )

        # Validate file type if it has required columns
        if (
            self.file_type in FILE_TYPES
            and len(FILE_TYPES[self.file_type].get("required_columns", [])) > 0
        ):
            file_type = FILE_TYPES[self.file_type]
            required_columns = set(file_type["required_columns"])
            version_columns = set(
                only_printable(c["name"])
                for c in self.versions.latest("created_at").analysis.columns
            )
            if not (required_columns <= version_columns):
                raise ValidationError(
                    f"The version is missing columns required for the "
                    f"{file_type['name']} type: "
                    f"{required_columns - version_columns}"
                )

    @property
    def valid_types(self):
        """
        Returns an array of file_types for which this file may be classified.
        Currently only considers the contents of the latest version.
        """

        valid_types = []
        # The columns contained in the latest version
        version_columns = set(
            only_printable(c["name"])
            for c in self.versions.latest("created_at").analysis.columns
        )
        for enum, file_type in FILE_TYPES.items():
            required_columns = set(file_type["required_columns"])
            if required_columns <= version_columns:
                valid_types.append(enum)

        return valid_types

    def __str__(self):
        return f'{self.kf_id}'

    @property
    def path(self):
        """
        Returns absolute path to file download endpoint
        """
        study_id = self.study.kf_id
        file_id = self.kf_id
        download_url = f'/download/study/{study_id}/file/{file_id}'
        return download_url


def _get_upload_directory(instance, filename):
    """
    Resolves the directory where a file should be stored
    """
    if settings.DEFAULT_FILE_STORAGE == "django_s3_storage.storage.S3Storage":
        prefix = f"{settings.UPLOAD_DIR}/{filename}"
        return prefix
    else:
        if instance.study is not None:
            bucket = instance.study.bucket
        else:
            bucket = instance.root_file.study.bucket
        directory = f"{settings.UPLOAD_DIR}/{bucket}/"
        return os.path.join(directory, filename)


def version_id():
    return kf_id_generator('FV')


def object_id():
    return version_id()


class Version(models.Model):
    class Meta:
        permissions = [
            (
                "view_my_version",
                "Can view all versions in studies user is a member of",
            ),
            (
                "add_my_study_version",
                "Can add versions to studies the user is a member of",
            ),
            ("change_version_meta", "Can change any version meta",),
            ("change_version_status", "Can change any version status",),
            (
                "change_my_version_meta",
                "Can change version meta in studies the user is a member of",
            ),
            (
                "change_my_version_status",
                "Can change version status in studies the user is a member of",
            ),
            ("extract_version_config", "Can extract any version config",),
            (
                "extract_my_version_config",
                (
                    "Can extract version config in studies "
                    "the user is a member of"
                ),
            ),
        ]

    kf_id = KFIDField(primary_key=True, default=version_id)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    key = models.FileField(upload_to=_get_upload_directory,
                           max_length=512,
                           help_text=('Field to track the storage location of '
                                      'the version'))
    file_name = models.CharField(
        max_length=1000,
        help_text=(
            "The name of the version's file as it was originally uploaded"
        ),
    )
    description = models.TextField(
        null=True,
        max_length=10000,
        help_text=(
            "Description of changes introduced to the file by this version"
        ),
    )
    state = models.CharField(
        max_length=3,
        choices=(
            ("PEN", "Pending Review"),
            ("APP", "Approved"),
            ("CHN", "Changes Needed"),
            ("PRC", "Processed"),
        ),
        default="PEN",
        help_text="The current state of this version",
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="versions",
        help_text="The user who originally created this Version",
    )
    created_at = models.DateTimeField(default=timezone.now,
                                      null=False,
                                      help_text='Time the version was created')
    size = models.BigIntegerField(
        validators=[
            MinValueValidator(0, 'File size must be a positive number')
        ],
        help_text='Size of the version in bytes')

    root_file = models.ForeignKey(
        File,
        null=True,
        related_name="versions",
        help_text=("The file that this version belongs to"),
        on_delete=models.CASCADE,
    )
    study = models.ForeignKey(
        Study,
        null=True,
        related_name="versions",
        help_text=("The study that this version belongs to"),
        on_delete=models.CASCADE,
    )

    @property
    def valid_types(self):
        """
        Returns an array of file_types for which this version may be classified
        """

        valid_types = []
        # The columns contained in the version
        version_columns = set(
            only_printable(c["name"]) for c in self.analysis.columns
        )
        for enum, file_type in FILE_TYPES.items():
            required_columns = set(file_type["required_columns"])
            if required_columns <= version_columns:
                valid_types.append(enum)

        return valid_types

    def __str__(self):
        return self.kf_id

    @property
    def path(self):
        """
        Returns absolute path to file download endpoint with version_id
        """
        # Currently, to generate a download path, we must have either:
        # A) a root file that is connected to a study
        # B) a root file that is not connected to a study but a version that is
        # Sometimes this is not possible because a version can be created
        # without a linked root file
        if not (self.root_file and (self.root_file.study or self.study)):
            return None
        study_id = self.root_file.study.kf_id
        file_id = self.root_file.kf_id
        version_id = self.kf_id
        download_url = (
            f"/download/study/{study_id}/file/{file_id}"
            f"/version/{version_id}"
        )
        return download_url


class DownloadToken(models.Model):
    """
    A DownloadToken is a shortly lived token that is issued to a user to allow
    them to provide to the download endpoint to download a file. Eg:
    /download/SD_00000000/file/SF_00000000?token=abcabcabc
    This token is only valid for the file which it was issued for and is
    immediately invalidated upon being used.
    """
    token = models.CharField(max_length=27,
                             default=partial(secrets.token_urlsafe, 20),
                             editable=False,
                             help_text='The value of the token')
    claimed = models.BooleanField(default=False, help_text='Whether the token'
                                  ' has been claimed for a download')
    created_at = models.DateTimeField(default=timezone.now,
                                      null=False,
                                      help_text='Time the token was created')
    root_version = models.ForeignKey(
        Version,
        related_name="version",
        help_text=("The version that this token was" " generated for"),
        on_delete=models.CASCADE,
    )

    @property
    def expired(self) -> bool:
        """
        If the token was created longer than the max DOWNLOAD_TOKEN_TTL ago,
        it is considered expired and no longer valid.
        """
        created_ts = datetime.timestamp(self.created_at)
        now_ts = datetime.timestamp(datetime.now())
        expiration = created_ts + settings.DOWNLOAD_TOKEN_TTL
        return now_ts > expiration

    def is_valid(self, obj: Version) -> bool:
        """
        A token is valid if:
        1) It has not expired
        2) It has not been claimed
        3) The requested version matches the one the token was generated for
        """
        return (
            not self.expired
            and not self.claimed
            and obj == self.root_version
        )

    def __str__(self):
        return f'Token for {self.root_version.kf_id}'


class DevDownloadToken(models.Model):
    """
    A DevDownloadToken is a persistant token generated to allow download to
    all files when provided to the download endpoint. Eg:
    /download/SD_00000000/file/SF_00000000?token=abcabcabc
    These tokens may only be generated by admin users
    """

    class Meta:
        permissions = [("list_all_version", "Can list all versions")]

    name = models.CharField(max_length=100,
                            unique=True,
                            editable=False,
                            help_text='Name describing the token')
    token = models.CharField(max_length=27,
                             default=partial(secrets.token_urlsafe, 20),
                             editable=False,
                             help_text='The value of the token')
    created_at = models.DateTimeField(default=timezone.now,
                                      null=False,
                                      help_text='Time the token was created')
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tokens",
        help_text="The user who originally created this token",
    )

    def __str__(self):
        return f'DevDownloadToken {self.name}'
