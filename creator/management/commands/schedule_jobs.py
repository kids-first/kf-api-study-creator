import django_rq
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError

from django.conf import settings

from creator.models import Job
from creator.tasks import (
    sync_cavatica_projects_task,
    sync_dataservice_studies_task,
    sync_buckets_task,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Setup scheduled jobs"

    def handle(self, *args, **options):
        logger.info("Setting up scheduled tasks")

        self.cavatica_scheduler = django_rq.get_scheduler("cavatica")
        self.dataservice_scheduler = django_rq.get_scheduler("dataservice")
        self.aws_scheduler = django_rq.get_scheduler("aws")

        jobs = list(self.cavatica_scheduler.get_jobs())
        logger.info(f"Found {len(jobs)} jobs scheduled on the Cavatica queue")
        self.setup_cavatica_sync()

        jobs = list(self.dataservice_scheduler.get_jobs())
        logger.info(
            f"Found {len(jobs)} jobs scheduled on the Dataservice queue"
        )
        self.setup_dataservice_sync()

        jobs = list(self.aws_scheduler.get_jobs())
        logger.info(f"Found {len(jobs)} jobs scheduled on the AWS queue")
        self.setup_buckets_sync()

    def setup_cavatica_sync(self):
        logger.info("Scheduling Cavatica Sync jobs")
        name = "cavatica_sync"
        description = "Syncronize Cavatica projects to the Study Creator"

        self.cavatica_scheduler.cancel("cavatica_sync")

        self.cavatica_scheduler.schedule(
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

    def setup_dataservice_sync(self):
        logger.info("Scheduling Dataservice Sync jobs")
        name = "dataservice_sync"
        description = "Syncronize Dataservice studies to the Study Creator"

        self.dataservice_scheduler.cancel("dataservice_sync")

        self.dataservice_scheduler.schedule(
            id=name,
            description=description,
            scheduled_time=datetime.utcnow(),
            func=sync_dataservice_studies_task,
            repeat=None,
            interval=300,
        )
        job, created = Job.objects.get_or_create(
            name=name, description=description, scheduler="dataservice"
        )
        job.save()

    def setup_buckets_sync(self):
        logger.info("Scheduling Buckets Sync jobs")
        name = "buckets_sync"
        description = "Syncronize Buckets to the Study Creator"

        self.aws_scheduler.cancel("buckets_sync")

        self.aws_scheduler.schedule(
            id=name,
            description=description,
            scheduled_time=datetime.utcnow(),
            func=sync_buckets_task,
            repeat=None,
            interval=900,
        )
        job, created = Job.objects.get_or_create(
            name=name, description=description, scheduler="aws"
        )
        job.save()
