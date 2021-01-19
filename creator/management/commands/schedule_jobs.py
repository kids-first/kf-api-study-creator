import django_rq
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError

from django.conf import settings

from creator.jobs.models import Job
from creator.releases.tasks import (
    sync_releases_task,
    scan_releases,
    scan_tasks,
)
from creator.tasks import (
    analyzer_task,
    sync_cavatica_projects_task,
    sync_dataservice_studies_task,
    sync_buckets_task,
    slack_notify_task,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Setup scheduled jobs"

    def handle(self, *args, **options):
        logger.info("Setting up scheduled tasks")

        self.default_scheduler = django_rq.get_scheduler("default")
        self.cavatica_scheduler = django_rq.get_scheduler("cavatica")
        self.dataservice_scheduler = django_rq.get_scheduler("dataservice")
        self.releases_scheduler = django_rq.get_scheduler("releases")
        self.aws_scheduler = django_rq.get_scheduler("aws")
        self.slack_scheduler = django_rq.get_scheduler("slack")

        jobs = list(self.default_scheduler.get_jobs())
        logger.info(f"Found {len(jobs)} jobs scheduled on the default queue")
        self.setup_analyzer()

        jobs = list(self.cavatica_scheduler.get_jobs())
        logger.info(f"Found {len(jobs)} jobs scheduled on the Cavatica queue")
        self.setup_cavatica_sync()

        jobs = list(self.dataservice_scheduler.get_jobs())
        logger.info(
            f"Found {len(jobs)} jobs scheduled on the Dataservice queue"
        )
        self.setup_dataservice_sync()

        jobs = list(self.releases_scheduler.get_jobs())
        logger.info(
            f"Found {len(jobs)} jobs scheduled on the Coordinator queue"
        )
        self.setup_coordinator_sync()
        self.setup_scan_releases()
        self.setup_scan_tasks()

        jobs = list(self.aws_scheduler.get_jobs())
        logger.info(f"Found {len(jobs)} jobs scheduled on the AWS queue")
        self.setup_buckets_sync()

        jobs = list(self.slack_scheduler.get_jobs())
        logger.info(f"Found {len(jobs)} jobs scheduled on the Slack queue")
        self.setup_slack_notify()

    def setup_analyzer(self):
        logger.info("Scheduling Analyzer jobs")
        name = "analyzer"
        description = "Analyze version in the Study Creator"

        self.default_scheduler.cancel("analyzer")

        self.default_scheduler.schedule(
            id=name,
            description=description,
            scheduled_time=datetime.utcnow(),
            func=analyzer_task,
            repeat=None,
            interval=3600,
        )
        job, created = Job.objects.get_or_create(
            name=name, description=description, scheduler="default"
        )
        job.scheduled = True
        job.save()

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
        job.scheduled = True
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
        job.scheduled = True
        job.save()

    def setup_coordinator_sync(self):
        logger.info("Scheduling Release Coordinator Sync jobs")
        name = "releases_sync"
        description = "Syncronize Release Coordinator releases"

        self.releases_scheduler.cancel("releases_sync")

        self.releases_scheduler.schedule(
            id=name,
            description=description,
            scheduled_time=datetime.utcnow(),
            func=sync_releases_task,
            repeat=None,
            interval=600,
        )
        job, created = Job.objects.get_or_create(
            name=name, description=description, scheduler="releases"
        )
        job.scheduled = True
        job.save()

    def setup_scan_releases(self):
        logger.info("Scheduling Scan Releases job")
        name = "scan_releases"
        description = "Scan active releases"

        self.releases_scheduler.cancel(name)

        self.releases_scheduler.schedule(
            id=name,
            description=description,
            scheduled_time=datetime.utcnow(),
            func=scan_releases,
            repeat=None,
            interval=60,
        )
        job, created = Job.objects.get_or_create(
            name=name, description=description, scheduler="releases"
        )
        job.scheduled = True
        job.save()

    def setup_scan_tasks(self):
        logger.info("Scheduling Scan Tasks job")
        name = "scan_tasks"
        description = "Scan active tasks"

        self.releases_scheduler.cancel(name)

        self.releases_scheduler.schedule(
            id=name,
            description=description,
            scheduled_time=datetime.utcnow(),
            func=scan_tasks,
            repeat=None,
            interval=30,
        )
        job, created = Job.objects.get_or_create(
            name=name, description=description, scheduler="releases"
        )
        job.scheduled = True
        job.save()

    def setup_buckets_sync(self):
        logger.info("Scheduling Buckets Sync jobs")
        name = "buckets_sync"
        description = "Syncronize Buckets to the Study Creator"

        self.aws_scheduler.cancel("buckets_sync")

        # This is a legacy job that never reached production
        self.aws_scheduler.cancel("inventories_sync")
        try:
            job = Job.objects.get(name="inventories_sync")
            job.delete()
        except Exception:
            # The job is no longer there
            pass

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
        job.scheduled = True
        job.save()

    def setup_slack_notify(self):
        logger.info("Scheduling Slack notification jobs")
        name = "slack_notify"
        description = "Send daily events to Slack channels"

        self.slack_scheduler.cancel(name)

        self.slack_scheduler.cron(
            "0 13 * * *",
            id=name,
            description=description,
            func=slack_notify_task,
        )
        job, created = Job.objects.get_or_create(
            name=name, description=description, scheduler="slack"
        )
        job.scheduled = True
        job.save()
