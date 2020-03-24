import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission

from creator.groups import GROUPS

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Setup permission groups"

    def handle(self, *args, **options):
        logger.info("Setting up permission groups")

        for group_name, permissions in GROUPS.items():
            g, created = Group.objects.get_or_create(
                name=group_name, defaults={"name": group_name}
            )
            if not created:
                logging.info(f"Group {g.name} already exists")
            else:
                logging.info(f"Group {g.name} was created")

            for code in permissions:
                logging.info(f"Adding permission {code} to group {g.name}")
                try:
                    p = Permission.objects.get(codename=code)
                    g.permissions.add(p)
                except Permission.DoesNotExist:
                    logger.error(f"could not find permission {code}")
                    pass
            g.save()
