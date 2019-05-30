from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser, BaseUserManager


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
    sub = models.CharField(
        max_length=150,
        unique=True,
        db_index=True,
        help_text="The subject of the JWT and primary user identifier",
    )
    ego_groups = ArrayField(models.CharField(max_length=100, blank=True))
    ego_roles = ArrayField(models.CharField(max_length=100, blank=True))

    objects = MyUserManager()

    @property
    def is_admin(self):
        return 'ADMIN' in self.ego_roles
