import requests
import re
from django.core.management.base import BaseCommand, CommandError
from creator.studies.factories import StudyFactory, BatchFactory
from creator.studies.models import Study

API = 'https://kf-study-creator.kidsfirstdrc.org/graphql'


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

        parser.add_argument('--investigator',
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

    def handle(self, *args, **options):
        api = options.get('api')
        headers = {"Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE1NjMzNzQ5NjQsImV4cCI6MTU2MzQ2MTM2NCwic3ViIjoiZTcwZjBhYWQtMmIzMC00NWE5LWFiZGQtMzQ4NjUzYjM5ZmYzIiwiaXNzIjoiZWdvIiwiYXVkIjpbXSwianRpIjoiZTk4NWRhZDgtMjZkZC00MjA1LTkwMjEtMDJlNTVkZWFkMjkxIiwiY29udGV4dCI6eyJ1c2VyIjp7Im5hbWUiOiJicm9tZW9kb2xseUBnbWFpbC5jb20iLCJlbWFpbCI6ImJyb21lb2RvbGx5QGdtYWlsLmNvbSIsInN0YXR1cyI6IkFwcHJvdmVkIiwiZmlyc3ROYW1lIjoiQmVuamFtaW4iLCJsYXN0TmFtZSI6IkRvbGx5IiwiY3JlYXRlZEF0IjoxNTMxNzg1NjAwMDAwLCJsYXN0TG9naW4iOjE1NjMzNzQ5NjQwMTAsInByZWZlcnJlZExhbmd1YWdlIjpudWxsLCJyb2xlcyI6WyJBRE1JTiJdLCJncm91cHMiOlsia2Ytc3Rha2Vob2xkZXIiXSwicGVybWlzc2lvbnMiOltdfX19.Z5kTTACl0Rrt-qMqMbPvgbjQFH_JzAqiLvnIQmbOn-AW7ZN76mMsx3_N0jvznacEY4a8E585tz0yn6_1e8QmaRdQHSqhaoFPNuh-rVv9W1ihpNAYlav7cpSmAnqqiIIsw_YQRewvqLasxy2qzq67oVyz1WaDshElYhFuXqr2P66ZWT1XiFvkNvxWdzN8G7IRWObr-Y5kmz98UdG_GvYs-7KZMoM4_jt_EHuS9GUU6OIFP17G109wEeM6ctoPt7LjkL2cYFiw3YwSbwztlKWY-z5UlNmymJVOAMAZgBngtSGR9ig4psQX0Fgx1a7Hvq6EBhf5fa6xPP50nruEn6q9iw"}

        query = """
            query Study($kfId: String!) {
                studyByKfId(kfId: $kfId) {
                  name
                  shortName
                  bucket
                  kfId
                  modifiedAt
                  createdAt
                }
            }
        """
        variables = {"kfId": "SD_46SK55A3"}
        # pull all data for study from prod
        results = self.run_query(headers, api, query, variables)

        if(results['data']['studyByKfId']):
            # clean up (kfId, name,short_name, bucket )

            study_values = {self.camel_to_snake(k): re.sub(r'hernia', options.get('investigator'), v, flags=re.I)
                            for (k, v) in results['data']['studyByKfId'].items()}
            print(study_values)

            # write study to db (update_or_create)

            new_study, created = Study.objects.update_or_create(
                defaults=study_values
            )
            if created:
                self.stdout.write("Created {}".format(variables['kfId']))
            else:
                self.stdout.write("Updated {}".format(variables['kfId']))
        else:
            self.stderr.write("No Results for {}".format(variables.kfId))
        # clean-up files (name, downloadUrl, description, kfId)

        # self.stdout.write(results['data']['studyByKfId']['name'])
