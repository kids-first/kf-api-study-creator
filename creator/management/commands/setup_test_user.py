import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.utils import IntegrityError
from creator.organizations.models import Organization

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
            organization, created = Organization.objects.get_or_create(
                id="da4cb83b-4649-4ac9-9745-337111b0f4b7",
                name="Magical Memes",
                defaults={
                    "website": "https://cataas.com",
                    "email": "admin@example.com",
                    "image": "https://cataas.com/cat",
                },
            )
            organization.save()
            user.organizations.add(organization)

            organization = Organization.objects.filter(
                name="Default Organization"
            ).first()

            if organization:
                user.organizations.add(organization)

            user.save()
        except Exception as err:
            logger.error(f"Problem occurred adding user as admin: {err}")
