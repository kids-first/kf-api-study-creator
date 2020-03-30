from django.core.management.base import BaseCommand, CommandError
from creator.studies.factories import StudyFactory


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

        n = options.get('n')
        if not n:
            n = 5
        r = StudyFactory.create_batch(n)
