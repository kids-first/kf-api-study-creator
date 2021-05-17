import uuid
import pytz
from datetime import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from creator.studies.models import Study
from creator.organizations.models import Organization
from django.contrib.auth.models import Group


User = get_user_model()


class ReferralToken(models.Model):
    """
    An ReferralToken will be exchanged by a new or existing user in order to
    be added to an organization and/or studies with a given role.
    """

    class Meta:
        permissions = [
            ("list_all_referraltoken", "Can view all referral tokens"),
        ]

    uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, primary_key=True
    )

    email = models.EmailField(
        max_length=254,
        help_text="The email that the token link will be sent to",
    )

    claimed = models.BooleanField(
        default=False, help_text="If the token has been used"
    )

    organization = models.ForeignKey(
        Organization,
        related_name="referral_tokens",
        help_text="The organization the user will be added to",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    studies = models.ManyToManyField(
        Study,
        related_name="referral_tokens",
        help_text="List of studies that the user will be added to",
    )

    groups = models.ManyToManyField(
        Group,
        blank=True,
        help_text="The role the user will assume in these studies",
        related_name="referral_tokens",
        related_query_name="referral_tokens",
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        null=False,
        help_text="Time the referral token was created",
    )

    claimed_by = models.ForeignKey(
        User,
        related_name="referral_tokens_claimed_by",
        help_text="The user who claims the token",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    created_by = models.ForeignKey(
        User,
        related_name="referral_tokens_created_by",
        help_text="The user who created the token",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    @property
    def is_valid(self):
        """
        If the token has already been claimed or if it has expired
        """

        exp_length = settings.REFERRAL_TOKEN_EXPIRATION_DAYS
        expired = (
            datetime.now().replace(tzinfo=pytz.UTC) - self.created_at
        ).days > exp_length
        return not self.claimed and not expired

    @property
    def invite_url(self):
        """
        User invitation url
        """
        return f"{settings.DATA_TRACKER_URL}/join?token={self.uuid}"
