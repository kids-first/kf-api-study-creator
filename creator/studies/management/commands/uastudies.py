import requests
import re
from django.core.management.base import BaseCommand, CommandError
from creator.studies.factories import StudyFactory, BatchFactory
from creator.studies.models import Study

API = 'https://kf-study-creator.kidsfirstdrc.org/graphql'
DATASERVICE = 'https://kf-api-dataservice.kidsfirstdrc.org'


class Command(BaseCommand):
    help = 'Make fake studies for usability testing'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--token',
                            help='JWT',
                            type=str)

        parser.add_argument('--api',
                            default=API,
                            help='Address of the data tracker graphql api',
                            type=str)

        parser.add_argument('-pi',
                            help='Name of investigator',
                            type=str)

    def camel_to_snake(self, text):
        str1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', str1).lower()

    def run_query(self, headers, api, query, variables):
        request = requests.post(api,
                                json={'query': query, 'variables': variables},
                                headers=headers
                                )
        if request.status_code == 200:
            return request.json()
        else:
            self.stderr.write("Query failed to run by returning code of {}. {}".format(
                request.status_code, query))

    def get_studies_by_pi(self, pi):
        # GET all studies
        resp = requests.get(f'{DATASERVICE}/studies?limit=100')
        studies = resp.json()['results']
        studies_investigator = []

        for study in studies:
            fields = study

            if fields['name'] is None:
                fields['name'] = ''

            fields['investigator'] = ''

            if fields['_links']['investigator']:
                # map GET _links.investigator to add the investigator name to the study response
                req = requests.get(
                    DATASERVICE+fields['_links']['investigator'])
                investigator = req.json()['results']['name']
                fields['investigator'] = investigator

            del fields['_links']
            studies_investigator.append(fields)

        # filter by --investigator
        investigators_studies = [
            study for study in studies_investigator
            if pi.lower() in study['investigator'].lower()
        ]
        for study in investigators_studies:
            del study['investigator']

        return investigators_studies

    def load_study(self, kfId, data, pi):
        new_study, created = Study.objects.update_or_create(
            defaults=data,
            kf_id=kfId
        )

        if created:
            print("Created {}: {}".format(pi, kfId))
        else:
            print("Updated {}: {}".format(pi, kfId))

    def load_test_study(self, investigator):
        # pull donw the Churn SD_46SK55A3 study and update a fake one
        resp = requests.get(f'{DATASERVICE}/studies/SD_46SK55A3')
        test_study = resp.json()['results']

        del test_study['kf_id']
        # get the second fake study and update it
        fake_study_id = Study.objects.get(kf_id='SD_KZRADNFE')
        self.stdout.write("Updating fake study {} with Chung SD_46SK55A3 study metadata".format(
            fake_study_id))
        self.load_study(fake_study_id, test_study, investigator)

    def handle(self, *args, **options):
        investigator = options.get('pi')

        self.load_test_study(investigator)

        self.stdout.write("Populating Studies from " +
                          investigator.upper())
        studies = self.get_studies_by_pi(investigator)
        # determinsiticly fetch study ids
        fake_study_ids = Study.objects.order_by('kf_id')[
            :len(studies)].values_list('kf_id')

        for idx, study in enumerate(studies):
            del study['kf_id']
            self.load_study(fake_study_ids[idx][0], study, investigator)
