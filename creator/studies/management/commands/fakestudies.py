from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from creator.studies.factories import StudyFactory
from creator.studies.models import Membership

User = get_user_model()


class Command(BaseCommand):
    help = 'Make fake studies'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('-n',
                            help='number of studies to make',
                            type=int)

    def handle(self, *args, **options):
        import factory.random
        factory.random.reseed_random('Fake data seed')

        study = StudyFactory(
            kf_id="SD_ME0WME0W",
            name="Mr. Meow's Memorable Meme Emporium",
            short_name="Cat Pics",
        )

        user = User.objects.get(username="testuser")
        member, _ = Membership.objects.get_or_create(
            collaborator=user, study=study
        )
        member.save()

        n = options.get('n')
        if not n:
            n = 5
        r = StudyFactory.create_batch(n)
