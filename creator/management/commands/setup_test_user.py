import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.utils import IntegrityError

User = get_user_model()

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Setup test user"

    def handle(self, *args, **options):
        logger.info("Making test user")

        try:
            User.objects.create_user("testuser", "test@example.com", "test")
        except IntegrityError:
            logger.info("user already exists")
        try:
            user = User.objects.get(username="testuser")
            user.first_name = "Bobby"
            user.last_name = "Tables"
            user.groups.add(Group.objects.get(name="Administrators"))
            user.save()
        except Exception as err:
            logger.error(f"Problem occurred adding user as admin: {err}")
