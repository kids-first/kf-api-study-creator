import os
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from creator.studies.models import Study


class File(models.Model):
    """
    The 'essence' of a file. Describes the ideal data, which underlying
    content may be iterated on as new 'versions'.
    """
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
                ('SAM', 'Sample Manifest'),
                ('SHM', 'Shipping Manifest'),
                ('CLN', 'Clinical Data'),
                ('FAM', 'Familial Relationships')),
            )

    def __str__(self):
        return f'{self.batch.study.kf_id} - {self.batch.name} - {self.name}'


def _get_upload_directory(instance, filename):
    """
    Resolves the directory where a file should be stored
    """
    directory = f'{settings.UPLOAD_DIR}/{instance.root_file.study.bucket}/'
    return os.path.join(directory, filename)


class Object(models.Model):
    key = models.FileField(upload_to=_get_upload_directory,
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
        return (f'{self.root_file.batch.study.kf_id} '
                f'- {self.root_file.batch.name} '
                f'- {self.root_file.name} '
                f'- {self.key}')
