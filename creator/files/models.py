import os
import uuid
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from creator.studies.models import Study
from creator.fields import KFIDField, kf_id_generator


def file_id():
    return kf_id_generator('SF')


class File(models.Model):
    """
    The 'essence' of a file. Describes the ideal data, which underlying
    content may be iterated on as new 'versions'.
    """
    kf_id = KFIDField(primary_key=True, default=file_id)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000,
                                   help_text='Description of the file')
    study = models.ForeignKey(Study,
                              related_name='files',
                              help_text='The study this file belongs to',
                              on_delete=models.CASCADE,)
    file_type = models.CharField(
            max_length=3,
            choices=(
                ('SEQ', 'Sequencing Manifest'),
                ('SHM', 'Shipping Manifest'),
                ('CLN', 'Clinical Data'),
                ('FAM', 'Familial Relationships')),
            )

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
    if settings.DEFAULT_FILE_STORAGE == 'django_s3_storage.storage.S3Storage':
        prefix = f'{settings.UPLOAD_DIR}/{filename}'
        return prefix
    else:
        directory = f'{settings.UPLOAD_DIR}/{instance.root_file.study.bucket}/'
        return os.path.join(settings.BASE_DIR, directory, filename)


def object_id():
    return kf_id_generator('FV')


class Object(models.Model):
    kf_id = KFIDField(primary_key=True, default=object_id)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    key = models.FileField(upload_to=_get_upload_directory,
                           max_length=512,
                           help_text=('Field to track the storage location of '
                                      'the object'))
    created_at = models.DateTimeField(default=timezone.now,
                                      null=False,
                                      help_text='Time the object was created')
    size = models.BigIntegerField(
            validators=[
                MinValueValidator(0, 'File size must be a positive number')
            ],
            help_text='Size of the object in bytes')

    root_file = models.ForeignKey(File,
                                  related_name='versions',
                                  help_text=('The file that this version '
                                             'object belongs to'),
                                  on_delete=models.CASCADE,)

    def __str__(self):
        return self.kf_id
