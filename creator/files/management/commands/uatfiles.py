import os
import requests
import pprint
from django.core.management.base import BaseCommand, CommandError
from creator.files.models import File, Version
from creator.studies.models import Study
from creator.models import User
from django.core.exceptions import ObjectDoesNotExist
pp = pprint.PrettyPrinter(indent=4)

API = 'https://kf-study-creator.kidsfirstdrc.org/graphql'


class Command(BaseCommand):
    help = 'Make fake files for usability testing'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('-token',
                            help='JWT',
                            type=str)

        parser.add_argument('-studyId',
                            default='SD_46SK55A3',  # Chung -  Congenital Diaphragmatic Hernia
                            help='SD_XXXXXXXXX id for study to load files from',
                            type=str)

        parser.add_argument('-destId',
                            default='SD_KZRADNFE',  # SD_KZRADNFE - stable FAKE kf_id for Chung:SD_46SK55A3
                            help='SD_XXXXXXXXX id for FAKE study to load files to',
                            type=str)

        parser.add_argument('-verbose',
                            default=False,
                            help='print entity dicts',
                            type=str)

    def run_query(self, query, variables, token):
        request = requests.post('https://kf-study-creator.kidsfirstdrc.org/graphql',
                                json={'query': query, 'variables': variables},
                                headers={
                                    "Authorization": "Bearer {}".format(token)}
                                )
        if request.status_code == 200:
            return request.json()
        else:
            self.stderr.write("Query failed to run by returning code of {}. {}".format(
                request.status_code, query))
            pprint(request.headers)

    def get_study_files_for(self, studyId, token):

        self.stdout.write("Getting Files for study {}".format(studyId))

        query = """
          query Files($study_KfId: String!){
 	        	allFiles(study_KfId: $study_KfId){
              files: edges{
                file: node{
                  kf_id: kfId
                  uuid
                  name
                  file_type: fileType
                  description
                  fileVersions: versions {
                    versions: edges {
                      file_version: node {
                        kf_id: kfId
                        uuid
                        file_name: fileName
                        description
                        state
                        size
                      }
                    }
                  }
                }
              }
            }
          }
        """

        results = self.run_query(
            query, {"study_KfId": studyId}, token)

        if(results['data']):
            return results['data']['allFiles']['files']

    def create_versions(self, study_name, file_fields, file_versions):

        for version in file_versions:
            version_fields = version['file_version']

            name, ext = os.path.splitext(
                version_fields['file_name'])

            version_w_relations = {
                **{k: v for (k, v) in version_fields.items() if k not in {'uuid'}},
                # random user
                'creator': User.objects.order_by("?").first(),
                # relate to Study object
                'root_file': File.objects.get(kf_id=file_fields['kf_id']),
                # point to empty file
                'key': "/app/creator/source/uploads/empty{}".format(ext)
            }

            # pp.pprint(version_w_relations)

            new_version, created = Version.objects.update_or_create(
                defaults=version_w_relations, uuid=version_fields['uuid'])

            if created:
                print("  |- Version {}".format(
                    file_fields['kf_id'], version_fields['kf_id']))
            else:
                print("Updated File Version {}:{}".format(
                    file_fields['kf_id'], version_fields['kf_id']))

    def handle(self, *args, **options):
        # start with a clean tables
        File.objects.all().delete()

        studyId = options.get('studyId')
        files = self.get_study_files_for(studyId, options.get('token'))

        self.stdout.write('Loading {} Files from {} to {}'.format(
            len(files), studyId, options.get('destId')))

        for file in files:

            file_fields = file['file']

            file_fields_default = {k: v for (k, v) in file_fields.items() if k not in {
                'fileVersions', 'uuid'}}

            file_w_study = {
                **file_fields_default,
                'study': Study.objects.get(pk=options.get('destId'))
            }

            # create upload dir w/ empty.* file
            # name, ext = os.path.splitext(
            #     file_fields['fileVersions']
            #     ['versions'][0]['file_version']['file_name'])

            # fake_uplaod_dir = "/app/creator/source/uploads/{}".format(
            #     Study.objects.get(pk=options.get('destId')).name
            # )
            # file_url = "{}/empty{}".format(fake_uplaod_dir, ext)

            # try:
            #     # Create target Directory
            #     os.mkdir(fake_uplaod_dir)
            #     print("Directory ", fake_uplaod_dir,  " Created ")
            #     open(file_url, 'w+')
            # except FileExistsError:
            #     print("Directory ", fake_uplaod_dir,  " already exists")
            #     open(file_url, 'w+')

            # pp.pprint(file_w_study)

            new_file, created = File.objects.update_or_create(
                defaults=file_w_study, uuid=file_fields['uuid'])

            if created:
                print("Created File {}".format(file_fields['kf_id']))
            else:
                print("Updated File {}".format(file_fields['kf_id']))

            self.create_versions(
                file_fields, file_fields['fileVersions']['versions'])
