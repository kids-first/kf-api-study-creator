import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from creator.releases.factories import ReleaseFactory, ReleaseServiceFactory

User = get_user_model()

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Make fake releases"

    def add_arguments(self, parser):
        parser.add_argument("-n", help="number of releases to make", type=int)

    def handle(self, *args, **options):
        import factory.random

        factory.random.reseed_random("Fake data seed")

        services = ReleaseServiceFactory.create_batch(3)

        n = options.get("n")
        if not n:
            n = 10
        logger.info(f"Creating {n} releases")

        r = ReleaseFactory.create_batch(n)
