import os
import logging
from pprint import pformat

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from kf_lib_data_ingest.common.io import read_json
from creator.organizations.models import Organization
from creator.studies.models import Study
from creator.data_templates.management.commands.faketemplates import (
    create_templates_from_workbook
)


User = get_user_model()

logger = logging.getLogger(__name__)

DATA_PATH = os.path.join("./demo/data.json")


class Command(BaseCommand):
    help = (
        "Make an org, study, and templates for a demo"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--data_file",
            default=DATA_PATH,
            type=str,
            help="Path to the data.json",
        )

    def handle(self, *args, **options):
        """
        Make fake org and study, add templates to all studies in org
        """
        data_path = options["data_file"]
        data_path = os.path.abspath(data_path)

        logger.info(f"Reading {data_path}")
        data = read_json(data_path)

        # Create org
        org_data = data["organization"]
        try:
            org = Organization.objects.get(id=org_data["id"])
        except Organization.DoesNotExist:
            org = Organization(**org_data)
            logger.info(f"Created organization {pformat(org_data)}")
        else:
            for attr, val in org_data.items():
                if attr == "id":
                    continue
                setattr(org, attr, val)
            logger.info(f"Updated organization {pformat(org_data)}")

        count, _ = org.data_templates.all().delete()
        logger.info(
            f"Deleted {count} templates in organization {org.name}"
        )
        org.save()

        user = User.objects.get(username="testuser")
        user.organizations.add(org)
        user.save()
        logger.info(f"Added testuser to organization {pformat(org.name)}")

        # Create study
        study_data = data["study"]
        try:
            study = Study.objects.get(pk=study_data["kf_id"])
            study.delete()
        except Study.DoesNotExist:
            pass
        study = Study(organization=org, **study_data)
        study.save()
        logger.info(f"Created study {pformat(study_data)}")

        # Create templates
        templates_path = data["template_package"]
        templates_path = os.path.abspath(templates_path)
        os.stat(templates_path)
        tvs = create_templates_from_workbook(templates_path, org)
        logger.info(f"Created {len(tvs)} templates")
