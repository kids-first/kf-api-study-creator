import django_rq
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError

from django.conf import settings

from creator.models import Job
from creator.tasks import sync_cavatica_projects_task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Setup scheduled jobs"

    def handle(self, *args, **options):
        logger.info("Setting up scheduled tasks")

        self.scheduler = django_rq.get_scheduler("cavatica")

        jobs = list(self.scheduler.get_jobs())

        logger.info(f"Found {len(jobs)} jobs scheduled on the Cavatica queue")

        self.setup_cavatica_sync()

    def setup_cavatica_sync(self):
        logger.info("Scheduling Cavatica Sync jobs")
        name = "cavatica_sync"
        description = "Syncronize Cavatica projects to the Study Creator"

        self.scheduler.cancel("cavatica_sync")

        self.scheduler.schedule(
            id=name,
            description=description,
            scheduled_time=datetime.utcnow(),
            func=sync_cavatica_projects_task,
            repeat=None,
            interval=300,
        )
        job, created = Job.objects.get_or_create(
            name=name, description=description, scheduler="cavatica"
        )
        job.save()
