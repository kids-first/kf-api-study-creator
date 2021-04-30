from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from creator.studies.factories import StudyFactory
from creator.studies.models import Membership
from creator.organizations.models import Organization

User = get_user_model()


class Command(BaseCommand):
    help = "Make fake studies"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("-n", help="number of studies to make", type=int)

    def handle(self, *args, **options):
        import factory.random

        factory.random.reseed_random("Fake data seed")

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

        study = StudyFactory(
            kf_id="SD_ME0WME0W",
            name="Mr. Meow's Memorable Meme Emporium",
            short_name="Cat Pics",
            organization=organization,
        )

        user = User.objects.get(username="testuser")
        member, _ = Membership.objects.get_or_create(
            collaborator=user, study=study
        )
        member.save()

        # Create default org and studies
        organization, created = Organization.objects.get_or_create(
            id="300d175a-4904-44e5-878b-e8ead565a082",
            name="Default Organization",
            defaults={
                "website": "https://kidsfirstdrc.org",
                "email": "admin@example.com",
                "image": (
                    "https://raw.githubusercontent.com/kids-first/"
                    "kf-ui-data-tracker/master/src/assets/logo.svg"
                ),
            },
        )
        organization.save()
        n = options.get("n")
        if not n:
            n = 5
        r = StudyFactory.create_batch(n, organization=organization)
