import os
import csv
import logging
import requests
from django.core.management.base import BaseCommand, CommandError

from django.conf import settings

logger = logging.getLogger(__name__)

ROOT_PROJECT_NS = "kidsfirst:"
ROOT_PROJECT_LOCAL_ID = "drc"
ROOT_PROJECT_ABBR = "KFDRC"
ROOT_PROJECT_NAME = (
    "The Gabriella Miller Kids First Pediatric Research Program"
)
ROOT_PROJECT_DESCRIPTION = """
A large-scale data resource to help researchers uncover new insights into the 
biology of childhood cancer and structural birth defects.
""".replace(
    "\n", ""
)
ROOT_PROJECT_URL = "https://kidsfirstdrc.org"

CONTACT_EMAIL = "support@kidsfirstdrc.org"
CONTACT_NAME = "Kids First Support"

# This is the prefix used for each sub-project in Kids First (Each study)
PROJECT_PREFIX = "Kids First: "

# This is a list of studies that are currently on the portal
# We will only add these studies to the submission by default
PUBLISHED_STUDIES = [
    "SD_DK0KRWK8",
    "SD_NMVV8A1Y",
    "SD_R0EPRSGS",
    "SD_7NQ9151J",
    "SD_YNSSAPHE",
    "SD_9PYZAHHE",
    "SD_DZ4GPQX6",
    "SD_W0V965XZ",
    "SD_ZXJFFMEF",
    "SD_M3DBXD12",
    "SD_8Y99QZJJ",
    "SD_46RR9ZR6",
    "SD_PREASA7S",
    "SD_B8X3C1MX",
    "SD_BHJXBDQK",
    "SD_1P41Z782",
    "SD_DYPMEHHF",
    "SD_RM8AFW0R",
    "SD_YGVA0E1C",
    "SD_6FPYJQBR",
    "SD_ZFGDG5YS",
    "SD_46SK55A3",
]


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

        # By default we will process all published studies
        self.studies = self.get_studies(options.get("studies"))

        # Write out some of the basic files
        self.write_id_namespace()
        self.write_project()
        self.write_contact()
        self.write_project_in_project()

        # Process each study's files individually and write them out
        self.write_file_header()
        self.files = []
        for study in self.studies:
            self.process_study_files(study)

    def get_studies(self, studies):
        """
        Retrieve studies and their info from the Dataservice and return them
        keyed by their ID
        """
        data = {}
        for study in studies:
            try:
                resp = requests.get(
                    f"{settings.DATASERVICE_URL}/studies/{study}"
                )
            except Exception as err:
                logger.error(
                    f"Problem getting study {study} from Dataservice: {err}"
                )
                raise
            data[study] = resp.json()["results"]
        return data

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

    def write_id_namespace(self):
        """"""
        logger.info("Writing namespace info")
        with open(
            os.path.join(self.out_dir, "id_namespace.tsv"), "w", newline="\n"
        ) as f:
            writer = csv.writer(f, delimiter="\t")
            # Header
            writer.writerow(["id", "abbreviation", "name", "description"])
            # Content
            writer.writerow(
                [
                    ROOT_PROJECT_NS,
                    ROOT_PROJECT_ABBR + "_NS",
                    "Namespace for " + ROOT_PROJECT_NAME,
                    "Namespace for " + ROOT_PROJECT_NAME,
                ]
            )

    def write_project(self):
        """
        Create projects, one for Kids first and one for each study.
        """
        logger.info("Writing project info")
        with open(
            os.path.join(self.out_dir, "project.tsv"),
            "w",
            newline="\n",
        ) as f:
            writer = csv.writer(f, delimiter="\t")
            # Header
            writer.writerow(
                [
                    "id_namespace",
                    "local_id",
                    "persistent_id",
                    "creation_time",
                    "abbreviation",
                    "name",
                    "description",
                ]
            )
            # The Kids First project itself
            writer.writerow(
                [
                    ROOT_PROJECT_NS,
                    ROOT_PROJECT_LOCAL_ID,
                    None,
                    None,
                    ROOT_PROJECT_ABBR,
                    ROOT_PROJECT_NAME,
                    ROOT_PROJECT_DESCRIPTION,
                ]
            )
            # Write a project for each study
            # logger.info(f"write study to projects {self.studies}")
            for kf_id, study in self.studies.items():
                print(study)
                writer.writerow(
                    [
                        ROOT_PROJECT_NS,
                        kf_id,
                        None,
                        None,
                        kf_id,
                        study["short_name"],
                        study["name"],
                    ]
                )

    def write_project_in_project(self):
        """
        Create subprojects, one for each Kids First study.
        """
        logger.info("Writing subproject info")
        with open(
            os.path.join(self.out_dir, "project_in_project.tsv"),
            "w",
            newline="\n",
        ) as f:
            writer = csv.writer(f, delimiter="\t")
            # Header
            writer.writerow(
                [
                    "parent_project_id_namespace",
                    "parent_project_local_id",
                    "child_project_id_namespace",
                    "child_project_local_id",
                ]
            )
            # Content
            for study in self.studies:
                writer.writerow(
                    [
                        ROOT_PROJECT_NS,
                        ROOT_PROJECT_LOCAL_ID,
                        ROOT_PROJECT_NS,
                        study,
                    ]
                )

    def process_study_files(self, study):
        files = self.gather_study(study)
        self.write_study_files(study, files)

    def gather_study(self, study):
        """
        Pull each study's genomic-files from the Dataservice and return them
        """
        logger.info(f"Fetching files for study {study}")
        results = []
        resp = requests.get(
            f"{settings.DATASERVICE_URL}/genomic-files?study_id={study}&visible=True&limit=100"
        )
        logger.info(f"{resp.json()['total']} files to fetch")
        results.extend(resp.json()["results"])
        while "next" in resp.json()["_links"]:
            next_link = resp.json()["_links"]["next"]
            resp = requests.get(
                f"{settings.DATASERVICE_URL}/{next_link}&visible=True&limit=100"
            )
            results.extend(resp.json()["results"])
            # Displays current status in fetching the files
            # print(f"\r{len(results)}/{resp.json()['total']}", end="")

        logger.info(f"Fetched {len(results)} files for study {study}")
        return results

    def write_contact(self):
        """
        Write the contact file with info for how the C2M2 submission was created
        """
        logger.info("Writing contact info")
        with open(
            os.path.join(self.out_dir, "primary_dcc_contact.tsv"),
            "w",
            newline="\n",
        ) as f:
            writer = csv.writer(f, delimiter="\t")
            # Header
            writer.writerow(
                [
                    "contact_email",
                    "contact_name",
                    "project_id_namespace",
                    "project_local_id",
                    "dcc_abbreviation",
                    "dcc_name",
                    "dcc_description",
                    "dcc_url",
                ]
            )
            # Content
            writer.writerow(
                [
                    CONTACT_EMAIL,
                    CONTACT_NAME,
                    ROOT_PROJECT_NS,
                    ROOT_PROJECT_LOCAL_ID,
                    ROOT_PROJECT_ABBR,
                    ROOT_PROJECT_NAME,
                    ROOT_PROJECT_DESCRIPTION,
                    ROOT_PROJECT_URL,
                ]
            )

    def write_file_header(self):
        """
        Write the header for file.tsv
        """
        with open(
            os.path.join(self.out_dir, "file.tsv"), "w", newline="\n"
        ) as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(
                [
                    "id_namespace",
                    "local_id",
                    "project_id_namespace",
                    "project_local_id",
                    "persistent_id",
                    "creation_time",
                    "size_in_bytes",
                    "uncompressed_size_in_bytes",
                    "sha256",
                    "md5",
                    "filename",
                    "file_format",
                    "data_type",
                    "assay_type",
                    "mime_type",
                ]
            )

    def write_study_files(self, study, files):
        with open(
            os.path.join(self.out_dir, "file.tsv"), "a", newline="\n"
        ) as f:
            writer = csv.writer(f, delimiter="\t")
            # Content
            for row in files:
                writer.writerow(
                    [
                        ROOT_PROJECT_NS,
                        row["kf_id"],
                        ROOT_PROJECT_NS,
                        study,
                        None,
                        None,
                        row["size"],
                        row["size"],
                        None,
                        row["hashes"].get("etag"),
                        self.filename_from_urls(row["urls"]),
                        None,
                        None,
                        None,
                        None,
                    ]
                )

    def filename_from_urls(self, urls):
        """
        Extracts the filename from the first url on the file.
        """
        if len(urls) == 0:
            raise ValueError("Expected genomic file to have at least one url")

        return urls[0].split("/")[-1]
