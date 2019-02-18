from django.db import models
from django.core.validators import RegexValidator
from creator.studies.models import Study


# From https://stackoverflow.com/questions/50480924/regex-for-s3-bucket-name
BUCKET_RE = (r'(?=^.{3,63}$)(?!^(\d+\.)+\d+$)(^(([a-z0-9]|[a-z0-9][a-z0-9\-]*'
             '[a-z0-9])\.)*([a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])$)')
KEY_RE = r'[A-Za-z0-9 !\-\_\.\*\'\(\)\/]+'


class FileEssence(models.Model):
    name = models.CharField(max_length=100)
    notes = models.TextField()
    study = models.ForeignKey(Study,
                              related_name='files',
                              on_delete=models.CASCADE,)

    def __str__(self):
        return self.name


class Object(models.Model):
    # The (study) bucket where the object is stored
    bucket = models.CharField(max_length=63,
                              validators=[RegexValidator(BUCKET_RE)])
    # The S3 object key
    key = models.CharField(max_length=1023,
                           validators=[RegexValidator(KEY_RE)])
    # S3 version id
    version_id = models.CharField(max_length=32)

    root_file = models.ForeignKey(FileEssence,
                                  related_name='versions',
                                  on_delete=models.CASCADE,)

    def __str__(self):
        return self.key
