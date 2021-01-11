import logging
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from creator.releases.models import ReleaseService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Setup count service"

    def handle(self, *args, **options):
        try:
            service = ReleaseService(
                kf_id="TS_00000000",
                name="Count Service",
                url="http://web:8080/countservice",
                description="An accounting service for Data Service entities",
                enabled=True,
            )
            service.save()
        except IntegrityError:
            logger.info("Service already exists")
