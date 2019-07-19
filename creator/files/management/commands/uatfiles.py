import requests
import pprint
from django.core.management.base import BaseCommand, CommandError
from creator.files.models import File, Version
from creator.studies.models import Study
from creator.models import User
from django.core.exceptions import ObjectDoesNotExist


API = 'https://kf-study-creator.kidsfirstdrc.org/graphql'


class Command(BaseCommand):
    help = 'Make fake files for usability testing'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--token',
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

    def run_query(self, query, variables, token):
        bearer_token = token or "eyJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE1NjM0ODI5ODYsImV4cCI6MTU2MzU2OTM4Niwic3ViIjoiZTcwZjBhYWQtMmIzMC00NWE5LWFiZGQtMzQ4NjUzYjM5ZmYzIiwiaXNzIjoiZWdvIiwiYXVkIjpbXSwianRpIjoiMTA0YTVhMzUtMmNjNS00M2NkLWFmMGYtNWZjN2IxM2YyYjA1IiwiY29udGV4dCI6eyJ1c2VyIjp7Im5hbWUiOiJicm9tZW9kb2xseUBnbWFpbC5jb20iLCJlbWFpbCI6ImJyb21lb2RvbGx5QGdtYWlsLmNvbSIsInN0YXR1cyI6IkFwcHJvdmVkIiwiZmlyc3ROYW1lIjoiQmVuamFtaW4iLCJsYXN0TmFtZSI6IkRvbGx5IiwiY3JlYXRlZEF0IjoxNTMxNzg1NjAwMDAwLCJsYXN0TG9naW4iOjE1NjM0ODI5ODY4MTUsInByZWZlcnJlZExhbmd1YWdlIjpudWxsLCJyb2xlcyI6WyJBRE1JTiJdLCJncm91cHMiOlsia2Ytc3Rha2Vob2xkZXIiXSwicGVybWlzc2lvbnMiOltdfX19.Bw-ssnnLGyb21JTry1YrL6gC419lD1wLPzsJupMyns-vmex0QCpnz_LT9mhDAZFXNDeLiMtvFoEOgakMEpANaba6nv2wOFXBdYdWJAmEYvZIqmwi4XKpimRzjgazvVkmD5jMFWGqBynRGyt8zn-cDpWbGzN4_mLPIkvqpX8F8rqtu2JpaPOXLg-EedeRkrSp0R8pzhjleH0WEvFZPlx4yS75JhOUWbNmT4Guscu2ZOiL4_1O6vOK2fD-uJ9N0bSVXDeCYfF1Pl-tF1DZMmebQGsmypwEzqDCpsCUu3LcIXD6p60LU4UJtFBLD-k9K3AL4ZmpfhW0hAm6vZb-Myc93w"
        request = requests.post('https://kf-study-creator.kidsfirstdrc.org/graphql',
                                json={'query': query, 'variables': variables},
                                headers={
                                    "Authorization": "Bearer {}".format(bearer_token)}
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
                        key
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

    def handle(self, *args, **options):
        studyId = options.get('studyId')
        files = self.get_study_files_for(studyId, options.get('token'))

        self.stdout.write('Loading {} Files from {} to {}'.format(
            len(files), studyId, options.get('destId')))

        File.objects.all().delete()

        for file in files:

            file_fields = file['file']

            file_versions = file_fields['fileVersions']['versions']

            del file_fields['fileVersions']

            # SD_KZRADNFE - stable FAKE kf_id for Chung:SD_46SK55A3
            file_study = Study.objects.get(pk=options.get('destId'))

            file_fields['study'] = file_study

            new_file, created = File.objects.update_or_create(
                defaults=file_fields, uuid=file_fields['uuid'])

            if created:
                print("Created File {}".format(file_fields['kf_id']))
            else:
                print("Updated File {}".format(file_fields['kf_id']))

            for version in file_versions:
                version_fields = version['file_version']

                version_fields['creator'] = User.objects.order_by(
                    "?").first()

                version_fields['root_file'] = File.objects.get(
                    kf_id=file_fields['kf_id'])

                new_version, created = Version.objects.update_or_create(
                    **version_fields)

                if created:
                    print("  |- Version {}".format(
                        file_fields['kf_id'], version_fields['kf_id']))
                else:
                    print("Updated File Version {}:{}".format(
                        file_fields['kf_id'], version_fields['kf_id']))
