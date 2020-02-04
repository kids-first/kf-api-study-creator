import django_rq
import logging
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError

from django.conf import settings

from creator.projects.cavatica import sync_cavatica_projects

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Setup scheduled jobs"

    def handle(self, *args, **options):
        logger.info("Setting up scheduled tasks")

        self.scheduler = django_rq.get_scheduler("cavatica")

        jobs = list(self.scheduler.get_jobs())

        logger.info(f"Found {len(jobs)} jobs scheduled on the Cavatica queue")

        if "cavatica_sync" not in self.scheduler:
            self.setup_cavatica_sync()
        else:
            logger.info("Cavatica Sync jobs have already been scheduled")

    def setup_cavatica_sync(self):
        logger.info("Scheduling Cavatica Sync jobs")

        self.scheduler.schedule(
            id="cavatica_sync",
            description="Syncronize Cavatica projects to the Study Creator",
            scheduled_time=datetime.utcnow(),
            func=sync_cavatica_projects,
            interval=300,
        )
