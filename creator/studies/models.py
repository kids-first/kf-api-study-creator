from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


# From https://stackoverflow.com/questions/50480924/regex-for-s3-bucket-name
BUCKET_RE = (r'(?=^.{3,63}$)(?!^(\d+\.)+\d+$)(^(([a-z0-9]|[a-z0-9][a-z0-9\-]*'
             '[a-z0-9])\.)*([a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])$)')


class Study(models.Model):
    """
    A study encompasses a group of participants subjected to similar analysis.
    """
    kf_id = models.CharField(max_length=11,
                             primary_key=True,
                             help_text='The Kids First Identifier',
                             null=False,)
    name = models.CharField(max_length=100,
                            help_text='The name of the study')
    visible = models.BooleanField(default=True,
                                  help_text='If the study is public or not')
    created_at = models.DateTimeField(auto_now_add=False,
                                      null=True,
                                      help_text='Time the study was created')
    bucket = models.CharField(max_length=63,
                              validators=[RegexValidator(BUCKET_RE)],
                              help_text='The s3 bucket name')


    def __str__(self):
        return self.kf_id


class Batch(models.Model):
    """
    A batch is an iteration of a study's data either through augmentation,
    alteration, or removal.
    """
    name = models.CharField(max_length=100,
                            help_text='The name of the batch')
    state = models.CharField(
        choices=(
            ('CON', 'configuring'),
            ('MAP', 'mapped'),
            ('SUB', 'submitted'),
            ('TRN', 'transformed')
        ),
        max_length=3,
        default='CON',
    )
    created_at = models.DateTimeField(default=timezone.now,
                                      help_text='Time the batch was created')

    study = models.ForeignKey(Study,
                              related_name='batches',
                              help_text='The study this batch belongs to',
                              on_delete=models.CASCADE,)


    def __str__(self):
        return self.name
