import requests
from django.core.management.base import BaseCommand, CommandError
from creator.studies.models import Study


API = 'https://kf-api-dataservice.kidsfirstdrc.org'


class Command(BaseCommand):
    help = 'Sync studies with the dataservice'

    def add_arguments(self, parser):
        parser.add_argument('--api',
                            default=API,
                            help='Address of the dataservice api',
                            type=str)

    def handle(self, *args, **options):
        api = options.get('api')
        env = 'prd'
        if '-dev' in api:
            env = 'dev'
        elif '-qa' in api:
            env = 'qa'

        bucket = f'kf-study-us-east-1-{env}-'

        resp = requests.get(f'{api}/studies?limit=100')
        studies = resp.json()['results']

        for study in studies:
            fields = study
            del fields['_links']

            if fields['name'] is None:
                fields['name'] = ''
            new_study, created = Study.objects.update_or_create(
                    defaults=fields,
                    kf_id=fields['kf_id'])
            s3_id = fields['kf_id'].lower().replace('_', '-')
            new_study.bucket = f"{bucket}{s3_id}"
            new_study.save()
            if created:
                print('Created', study['kf_id'])
            else:
                print('Updated', study['kf_id'])
