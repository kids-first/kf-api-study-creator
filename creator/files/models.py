from django.db import models
from django.core.validators import RegexValidator
from creator.studies.models import Study


KEY_RE = r'[A-Za-z0-9 !\-\_\.\*\'\(\)\/]+'


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
    key = models.CharField(max_length=1023,
                           help_text='The s3 key where this object is located',
                           validators=[RegexValidator(KEY_RE)])
    version_id = models.CharField(max_length=32,
                                  help_text='The s3 version id of this object')

    root_file = models.ForeignKey(FileEssence,
                                  related_name='versions',
                                  help_text=('The file that this version '
                                             'object belongs to'),
                                  on_delete=models.CASCADE,)
    created_at = models.DateTimeField(auto_now_add=True,
                                      null=False,
                                      help_text='Time the object was created')

    def __str__(self):
        return (f'{self.root_file.study.kf_id} '
                f'- {self.root_file.name} '
                f'- {self.key}')
