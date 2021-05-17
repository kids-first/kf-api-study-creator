import random
from django.core.management.base import BaseCommand, CommandError
from creator.files.factories import FileFactory, VersionFactory
from creator.studies.models import Study
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
        FileFactory.reset_sequence()
        VersionFactory.reset_sequence()

        n = options.get('n')
        if not n:
            n = 20

        # Using create_batch() on the FileFactory causes one study to be
        # created for each file generated. We want to only have a handful of
        # studies so we select all existing studies and randomly choose from
        # those instead of having the FileFactory create them. In the future,
        # we should be able to simply run 'fakestudies' and have the
        # StudyFactory create files for us rather than running both
        # 'fakestudies' and 'fakefiles'
        studies = Study.objects.all()
        for _ in range(n):
            study = random.choice(studies)
            r = FileFactory(study=study)
