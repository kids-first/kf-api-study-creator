from django.core.management.base import BaseCommand, CommandError
from creator.files.factories import FileFactory, VersionFactory
import factory


class Command(BaseCommand):
    help = 'Make fake files'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('-n',
                            help='number of files to make',
                            type=int)

    def handle(self, *args, **options):
        factory.random.reseed_random("Fake data seed")
        FileFactory.study.reset()
        FileFactory.reset_sequence()
        VersionFactory.reset_sequence()

        n = options.get('n')
        if not n:
            n = 20
        r = FileFactory.create_batch(n)
