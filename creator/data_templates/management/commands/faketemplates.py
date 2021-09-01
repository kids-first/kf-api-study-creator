import os
import logging
from pprint import pformat

import pandas
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from creator.data_templates.models import (
    DataTemplate,
    TemplateVersion
)
from creator.organizations.models import Organization
from kf_lib_data_ingest.common.io import read_df

User = get_user_model()

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_PATH = os.path.join(TEMPLATES_DIR, "template_package.xlsx")


def create_templates_from_workbook(templates_path, org):
    """
    Load templates from a template package and add the templtaes to all
    studies within an organization
    """
    # Parse table of contents
    toc = read_df(templates_path).to_dict(orient="records")

    # Create templates
    tvs = []
    for toc_entry in toc:
        template_name = toc_entry["Template Name"]
        template_description = toc_entry["Template Description"]
        fields_sheet = toc_entry["Sheets"].split("\n")[0]

        logger.info(
            f"Reading template {fields_sheet} from "
            f"{os.path.basename(templates_path)}"
        )
        dt = DataTemplate(
            organization=org,
            name=template_name,
            description=template_description
        )
        dt.save()
        tv = TemplateVersion(
            data_template=dt,
            description="Initial version",
        )
        tv.field_definitions = TemplateVersion.load_field_definitions(
            templates_path, sheet_name=fields_sheet
        )
        tv.save()
        tv.studies.set(org.studies.all())
        tv.save()

        tvs.append(tv)

        logger.info(
            f"Added {template_name} to org {org.name} studies: "
            f"{pformat([s.pk for s in tv.studies.all()])}"
        )
    return tvs


class Command(BaseCommand):
    help = (
        "Make fake (but realistic) data templates for all studies within an "
        "organization"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "name",
            help="Name of organization whose studies will be linked to all "
            "created templates",
            type=str
        )
        parser.add_argument(
            "--delete",
            action='store_true',
            help="Delete all templates in the organization before creating "
            " new ones",
        )
        parser.add_argument(
            "--template-package",
            default=TEMPLATES_PATH,
            type=str,
            help="Path to the template package",
        )

    def handle(self, *args, **options):
        """
        Make fake templates for an organization. Optionally delete all
        templates within org before creating new ones
        """
        org_name = options["name"]
        org = Organization.objects.filter(name=org_name).first()
        if not org:
            raise Organization.DoesNotExist(
                f"Organization with name {org_name} does not exist!"
            )

        if options["delete"]:
            count, _ = org.data_templates.all().delete()
            logger.info(
                f"Deleted {count} templates in organization {org.name}"
            )

        templates_path = options["template_package"]
        templates_path = os.path.abspath(templates_path)

        # Hack to check if path exists since read_df masks the
        # FileNotFoundError with an unsupported file type exception
        os.stat(templates_path)

        # Create templates
        logger.info(f"Creating templates for {org.name} from {templates_path}")
        tvs = create_templates_from_workbook(templates_path, org)
        logger.info(f"Created {len(tvs)} templates")
