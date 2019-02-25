from django.core.management.base import BaseCommand, CommandError
from creator.files.factories import FileFactory


class Command(BaseCommand):
    help = 'Make fake files'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('-n',
                            help='number of files to make',
                            type=int)

    def handle(self, *args, **options):
        n = options.get('n')
        if not n:
            n = 5
        r = FileFactory.create_batch(n)
