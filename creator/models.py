import uuid
import pytz
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
        user = self.model(username=username, email=self.normalize_email(email))

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
        return self.groups.filter(name="Administrators").exists()

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
