import os
import json
import logging
import requests
from dataclasses import dataclass, field
from typing import (
    Any,
    TypeVar,
    Dict,
    Generic,
    Optional,
    Union,
    List,
    get_args,
)
from django.core.management.base import BaseCommand, CommandError

from django.conf import settings

from creator.c2m2_submissions import entities
from creator.c2m2_submissions.datapackage import DATAPACKAGE
from creator.c2m2_submissions.globals import PUBLISHED_STUDIES

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create C2M2 Level 0 Manifest from Dataservice"

    def add_arguments(self, parser):
        parser.add_argument(
            "--studies",
            type=str,
            default=PUBLISHED_STUDIES,
            nargs="*",
            help="kf_ids of studies to include in the submission file",
        )
        parser.add_argument(
            "--out-dir",
            type=str,
            default="c2m2_submission",
            help="The directory to place the submission files in",
        )

    def handle(self, *args, **options):
        logger.info(
            f"Will build a submission file for {len(options.get('studies'))} "
            "studies."
        )
        self.out_dir = options.get("out_dir")
        self.setup_directory()

        mapper = EDAMMapper()
        mapper.write(self.out_dir)

        self.tables = [
            entities.Table[entity](out_dir=self.out_dir)
            for entity in [
                entities.Anatomy,
                entities.AssayType,
                entities.Biosample,
                entities.BiosampleFromSubject,
                entities.BiosampleInCollection,
                entities.Collection,
                entities.CollectionDefinedByProject,
                entities.CollectionInCollection,
                entities.File,
                entities.FileDescribesBiosample,
                entities.FileDescribesSubject,
                entities.FileInCollection,
                entities.IdNamespace,
                entities.NCBITaxonomy,
                entities.PrimaryDCCContact,
                entities.Project,
                entities.ProjectInProject,
                entities.Subject,
                entities.SubjectInCollection,
                entities.SubjectRoleTaxonomy,
            ]
        ]

        logger.info("Preparing files")
        for table in self.tables:
            table.prepare_file()

        # Write out the Kids First high-leve project
        projects = entities.Table[entities.Project](out_dir=self.out_dir)
        projects.load_entities()
        projects.write_entities()

        for study in PUBLISHED_STUDIES[:2]:
            logger.info(f"Compiling study '{study}'")
            for table in self.tables:
                table.load_entities(study)
                table.write_entities()

    def setup_directory(self):
        logger.info(f"Making directory for submission at '{self.out_dir}'")
        try:
            os.mkdir(self.out_dir)
        except FileExistsError:
            logger.warn(
                f"Output directory '{self.out_dir}' already exists."
                "May overwrite any previous contents"
            )
            pass

        logger.info(f"Placing datapackage file")
        with open(
            os.path.join(self.out_dir, "C2M2_datapackage.json"), "w"
        ) as f:
            json.dump(DATAPACKAGE, f)
