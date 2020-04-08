import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission

from creator.groups import GROUPS

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Setup permission groups"

    def handle(self, *args, **options):
        logger.info("Setting up permission groups")

        for group_name, permissions in GROUPS.items():
            g, created = Group.objects.get_or_create(
                name=group_name, defaults={"name": group_name}
            )
            if not created:
                logger.info(f"Group {g.name} already exists")
            else:
                logger.info(f"Group {g.name} was created")

            try:
                permissions = Permission.objects.filter(
                    codename__in=permissions
                ).all()
                g.permissions.set(permissions, clear=True)
                logger.info(f"Updated permissions for group {g.name}")
            except Exception as err:
                logger.error(f"Error updating permissions for group {g.name}")
                pass
            g.save()
