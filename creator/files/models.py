from django.db import models
from django.core.validators import MinValueValidator
from creator.studies.models import Study


class FileEssence(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000,
                                   help_text='Description of the file')
    study = models.ForeignKey(Study,
                              related_name='files',
                              help_text='The study this file belongs to',
                              on_delete=models.CASCADE,)

    def __str__(self):
        return f'{self.study.kf_id} - {self.name}'


class Object(models.Model):
    key = models.FileField(upload_to='uploads/',
                           help_text=('Field to track the storage location of '
                                      'the object'))
    created_at = models.DateTimeField(auto_now_add=True,
                                      null=False,
                                      help_text='Time the object was created')
    size = models.BigIntegerField(
            validators=[
                MinValueValidator(0, 'File size must be a positive number')
            ],
            help_text='Size of the object in bytes')

    root_file = models.ForeignKey(FileEssence,
                                  related_name='versions',
                                  help_text=('The file that this version '
                                             'object belongs to'),
                                  on_delete=models.CASCADE,)

    def __str__(self):
        return (f'{self.root_file.study.kf_id} '
                f'- {self.root_file.name} '
                f'- {self.key}')
