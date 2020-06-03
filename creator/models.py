import pytz
import django_rq
from datetime import datetime
from rq.job import Job as RQJob
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from creator.studies.models import Study


class MyUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        user = self.model(
            username=username,
            ego_groups=[],
            ego_roles=[],
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            username=username,
            email=self.normalize_email(email),
        )
        user.is_superuser = True
        user.ego_groups = []
        user.ego_roles = ['ADMIN']
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    """
    Stores only basic information about the user, namely their primary id
    that may be used to fetch their full profile.
    """
    class Meta:
        permissions = [("list_all_user", "Can list all users")]

    USERNAME_FIELD = "sub"
    # This overrides the AbstractUser username which has a unique contraint
    # on it in preference of the sub being the unique field.
    username = models.CharField(_("username"), max_length=150, unique=False)

    sub = models.CharField(
        max_length=150,
        unique=True,
        db_index=True,
        help_text="The subject of the JWT and primary user identifier",
    )
    ego_groups = ArrayField(models.CharField(max_length=100, blank=True))
    ego_roles = ArrayField(models.CharField(max_length=100, blank=True))
    picture = models.CharField(max_length=500, blank=True)
    slack_notify = models.BooleanField(
        default=False,
        help_text="Whether the user has enabled slack notifications",
    )
    slack_member_id = models.CharField(
        default="",
        blank=True,
        max_length=10,
        help_text="The user's slack member id",
    )
    study_subscriptions = models.ManyToManyField(
        Study, help_text="Tracks studies that user is following"
    )
    email_notify = models.BooleanField(
        default=False,
        help_text="Whether the user has enabled email notifications",
    )

    objects = MyUserManager()

    @property
    def is_admin(self):
        return 'ADMIN' in self.ego_roles

    @property
    def display_name(self):
        """
        Display user first name last name if exist, and username if not
        """
        user_name = self.username if self.username else "Unknown user"
        user_full_name = (
            (
                (self.first_name + " " if self.first_name else "")
                + (self.last_name if self.last_name else "")
            )
            if (self.first_name or self.last_name)
            else user_name
        )
        return user_full_name.strip()


class Job(models.Model):
    """
    Logs the current state of any scheduled, recurrent jobs.
    """

    class Meta:
        permissions = [
            ("view_settings", "Can view settings"),
            ("view_queue", "Can view queues"),
        ]

    name = models.CharField(
        primary_key=True,
        max_length=400,
        null=False,
        help_text="The name of the scheduled job",
    )
    scheduler = models.CharField(
        max_length=400,
        null=False,
        help_text="The scheduler the Job will run on",
    )
    description = models.TextField(
        null=True, help_text="Description of the Job's role"
    )
    active = models.BooleanField(
        default=True, help_text="If the Job is active"
    )
    failing = models.BooleanField(
        default=False, help_text="If the Job is failing"
    )
    created_on = models.DateTimeField(
        auto_now_add=True, null=False, help_text="Time the Job was created"
    )
    last_run = models.DateTimeField(null=True, help_text="Time of last run")
    last_error = models.TextField(
        null=True, help_text="Error message from last failure"
    )

    @property
    def enqueued_at(self):
        """ Returns the next scheduled run time for the job """
        scheduler = django_rq.get_scheduler(self.scheduler)
        ts = scheduler.connection.zscore(
            "rq:scheduler:scheduled_jobs", self.name
        )
        dt = datetime.fromtimestamp(ts)
        return dt.replace(tzinfo=pytz.UTC)
