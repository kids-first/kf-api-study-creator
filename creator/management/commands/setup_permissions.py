import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Setup permission groups"

    def handle(self, *args, **options):
        logger.info("Setting up permission groups")

        groups = [
            "Administrators",
            "Developers",
            "Investigators",
            "Bioinformatics",
        ]

        for group_name in groups:
            g, created = Group.objects.get_or_create(
                name=group_name, defaults={"name": group_name}
            )
            if not created:
                logging.info(f"Group {g.name} already exists")
            else:
                logging.info(f"Group {g.name} was created")
