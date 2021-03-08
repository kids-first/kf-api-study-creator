import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from creator.studies.factories import StudyFactory
from creator.studies.models import Membership

User = get_user_model()


class Command(BaseCommand):
    help = "Make fake studies"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("-n", help="number of studies to make", type=int)

    def handle(self, *args, **options):
        import factory.random

        factory.random.reseed_random("Fake data seed")

        study = StudyFactory(
            kf_id="SD_ME0WME0W",
            name="Mr. Meow's Memorable Meme Emporium",
            short_name="Cat Pics",
            visible=True,
            deleted=False,
        )

        if settings.DATASERVICE_URL:
            self.setup_dataservice(study)

        user = User.objects.get(username="testuser")
        member, _ = Membership.objects.get_or_create(
            collaborator=user, study=study
        )
        member.save()

        n = options.get("n")
        if not n:
            n = 5
        r = StudyFactory.create_batch(n)

    def setup_dataservice(self, study):
        requests.post(
            f"{settings.DATASERVICE_URL}/studies",
            json={
                "kf_id": "SD_ME0WME0W",
                "name": study.name,
                "external_id": study.external_id,
                "short_name": study.short_name,
            },
        )

        resp = requests.post(
            f"{settings.DATASERVICE_URL}/sequencing-centers",
            json={"kf_id": "SC_00000000", "name": "Sequencing Center"},
        )

        for i in range(10):
            resp = requests.post(
                f"{settings.DATASERVICE_URL}/participants",
                json={
                    "kf_id": f"PT_{i:08}",
                    "external_id": f"Participant {i}",
                    "study_id": study.kf_id,
                },
            )
            resp = requests.post(
                f"{settings.DATASERVICE_URL}/biospecimens",
                json={
                    "kf_id": f"BS_{i:08}",
                    "participant_id": f"PT_{i:08}",
                    "sequencing_center_id": "SC_00000000",
                    "analyte_type": "DNA",
                },
            )
