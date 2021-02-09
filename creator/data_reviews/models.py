from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class DataReview(models.Model):
    """
    The iterative process between a data contributor and the Data Resource 
    Center where study data is continually supplied, validated, and refined 
    to meet quality standards.
    """

    class Meta:
        permissions = [
            ("list_all_datareview", "Show all data_reviews"),
        ]

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=False,
        help_text="Time when the data_review was created"
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="data_reviews",
        help_text="The user who created the data review",
    )
