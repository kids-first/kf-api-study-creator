from django.db import models


class {{ model_name }}(models.Model):
    """
    Plug the model in here
    """

    class Meta:
        permissions = [
            ("list_all_{{ permission_singular }}", "Show all {{ plural }}"),
        ]

    created_at = models.DateTimeField(
        null=False, help_text="Time when the {{ singular }} was created"
    )
