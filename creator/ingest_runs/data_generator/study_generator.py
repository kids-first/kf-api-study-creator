"""
A fake KF study generator that generates realistic Data Service studies
Used to setup unit tests for ingest runs and related functionality

1. (Optional) Delete all previously generated data on disk, then 
   delete study in Data Service
2. Create a study ingest package at
<StudyGenerator.working_dir>/<StudyGenerator.study_id>_ingest_package
3. Read existing or create new study data files representing a minimal study
    - bio_manifest.tsv
    - sequencing_manifest.tsv
    - s3_source_gf_manifest.tsv
    - s3_harmonized_gf_manifest.tsv
    - gwo_manifest.tsv
4. Load study and sequencing center in Data Service
5. Ingest study data files into Data Service using ingest library
"""
import os
import datetime
import logging
import shutil
import string
import uuid
import random as ra
from pprint import pformat

from django.conf import settings
import requests
import pandas as pd

from d3b_utils.requests_retry import Session
from kf_lib_data_ingest.common.io import read_df
from kf_lib_data_ingest.common import pandas_utils
from kf_lib_data_ingest.app import settings as ingest_settings
from kf_lib_data_ingest.etl.ingest_pipeline import DataIngestPipeline
from kf_utils.dataservice.scrape import yield_kfids

from creator.fields import kf_id_generator

# For data generation
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
INGEST_PKG_TEMPLATE = os.path.join(ROOT_DIR, "ingest_package")
DEFAULT_STUDY_ID = "SD_ME0WME0W"
BROAD_SC_CENTER = "Broad Institute"
BROAD_KF_ID = "SC_DGDDQVYR"
SOURCE_GF_EXTS = [".cram", ".crai", ".cram.md5"]
HARM_GF_EXT = ".g.vcf.gz"
DEFAULT_SPECIMENS = 10
# DO NOT RE-ORDER - needed for deletion in StudyGenerator.clean
ENDPOINTS = [
    "read-groups",
    "read-group-genomic-files",
    "sequencing-experiments",
    "sequencing-experiment-genomic-files",
    "genomic-files",
    "biospecimen-genomic-files",
    "biospecimens",
    "outcomes",
    "phenotypes",
    "diagnoses",
    "participants",
    "family-relationships",
    "families",
    "studies",
]


class StudyGenerator(object):
    def __init__(
        self,
        working_dir=None,
        dataservice_url=None,
        study_id=DEFAULT_STUDY_ID,
        total_specimens=DEFAULT_SPECIMENS,
    ):
        """
        Constructor

        :param working_dir: the directory where the study ingest package along
        with data files will be written. Defaults to current working directory
        :type working_dir: str
        :param study_id: Kids First study_id to use when creating the study
        :type study_id: str
        :param dataservice_url: URL of Data Service where study will be loaded
        :type dataservice_url: str
        :param total_specimens: See _generate_files for details on how this
        is used.
        :type total_specimens: int
        """
        self.logger = logging.getLogger(type(self).__name__)
        self.dataservice_url = dataservice_url or settings.DATASERVICE_URL

        self.study_id = study_id
        self.total_specimens = total_specimens

        # Setup dirs
        if not working_dir:
            self.working_dir = os.getcwd()
        else:
            self.working_dir = os.path.abspath(working_dir)
        self.ingest_package_dir = os.path.join(
            self.working_dir, f"{self.study_id}_ingest_package"
        )
        self.data_dir = os.path.join(self.ingest_package_dir, "data")

        # Use default ingest settings - KF Data Service
        self.ingest_settings = ingest_settings.load().TARGET_API_CONFIG

        # For loading data into Data Service
        self.session = None
        self.id_prefixes = {
            "family": "FM",
            "participant": "PT",
            "biospecimen": "BS",
            "genomic_file": "GF",
        }
        self.dataframes = {}

    @property
    def study_bucket(self):
        """ Return study bucket from study KF ID """
        return (
            f"kf-study-us-east-1-dev-{self.study_id.lower().replace('_', '-')}"
        )

    def ingest_study(self, clean=True):
        """
        Entrypoint. Ingest study data into Data Service:

        1. Create study and sequencing center in Data Service
        2. Create a study ingest package in _working_dir_ named
        <study_id>_ingest_package
        2. Read or create new clinical data file in ingest package
        3. Read or create new genomic data files in ingest package
        4. Ingest study data files into Data Service

        See _generate_files_ for details on data files

        OPTIONAL - Cleanup before doing anything else:

        1. Delete study data in Data Service
        2. Delete study ingest package (includes data files) 

        See _clean_ for details on clean up operations

        :param clean: Whether or not to clean before running ingest. See
        _clean_ for details
        :type clean: bool
        """
        # Cleanup all previously written and loaded data
        if clean:
            self.clean()

        # Create study data files
        self.generate_files()

        # Load study, sequencing center into Data Service
        self.initialize_study()

        # Ingest study data files into Data Service
        self.run_ingest_pipeline()

        # Ensure all kf_ids were loaded and entity counts are valid
        self._assert_load()

    def clean(self, all_studies=False):
        """
        Clean up data before ingestion begins

        1. Delete study data in Data Service
        2. Delete existing ingest package with data files

        :param all_studies: Whether or not to delete all studies' data in
        Data Service. If False, will only delete entities linked to _study_id
        """
        self.logger.info("Clean up before study generation begins")

        # Delete entities in Data Service
        study_id = None if all_studies else self.study_id
        delete_entities(
            self.dataservice_url, study_id=study_id, logger=self.logger
        )

        # Delete existing data files
        self.logger.info("Deleting data files previously generated")
        for dir_ in [self.ingest_package_dir]:
            self.logger.info(f"Deleting files in {dir_}")
            shutil.rmtree(dir_, ignore_errors=True)

    def generate_files(self):
        """
        Generate clinical and genomic data files for a test study.
        Read files into DataFrames if they exist, otherwise create them:

        1. bio_manifest.tsv
        2. sequencing_manifest.tsv
        3. s3_source_gf_manifest.tsv
        4. s3_harmonized_gf_manifest.tsv
        5. gwo_manifest.tsv

        Files are written to <working_dir>/<study_id>_ingest_package/data
        """
        self.expected_counts = {
            "families": 2,
            "participants": self.total_specimens,
            "biospecimens": self.total_specimens,
            "sequencing-experiments": self.total_specimens,
            # Include only source gfs since harmonized gfs don't get loaded
            # by study generator
            "genomic-files": self.total_specimens * len(SOURCE_GF_EXTS),
        }
        self.logger.info(
            f"Creating clinical and genomic files for {self.study_id}. "
            f"Entities:\n{pformat(self.expected_counts)}"
        )

        # Create ingest package and data dir if it doesn't exist
        if not os.path.exists(self.ingest_package_dir):
            shutil.copytree(
                INGEST_PKG_TEMPLATE, self.ingest_package_dir
            )
            os.makedirs(self.data_dir, exist_ok=True)

        # Read or create data files
        fns = {
            "bio_manifest.tsv": self._create_bio_manifest,
            "sequencing_manifest.tsv": self._create_sequencing_manifest,
            "s3_source_gf_manifest.tsv": (
                self._create_s3_gf_manifest, False
            ),
            "s3_harmonized_gf_manifest.tsv": (
                self._create_s3_gf_manifest, True
            ),
            "gwo_manifest.tsv": self._create_bix_gwo_manifest,
        }

        for fn, create_func in fns.items():
            fp = os.path.join(self.data_dir, fn)
            # Read from disk
            if os.path.exists(fp):
                verb = "Reading"
                df = read_df(fp)
            else:
                # Write to disk
                verb = "Creating"
                if "gf_manifest" in fn:
                    create_func, harmonized = create_func
                    df = create_func(harmonized=harmonized)
                else:
                    df = create_func()
                    self.logger.info(f"{verb} {fn.split('.')[0]}. Path: {fp}")
                df = pd.DataFrame(df)
                df.to_csv(fp, sep='\t', index=False)
            self.dataframes[fn] = df

    def initialize_study(self):
        """
        Create study, sequencing_center entities in Data Service
        """
        if not self.session:
            self.session = Session()

        self.logger.info(
            f"Initializing study {self.study_id} in "
            f"Data Service {self.dataservice_url}"
        )
        payloads = [
            {
                "kf_id": self.study_id,
                "name": self.study_id,
                "external_id": self.study_id,
                "endpoint": "studies"
            },
            {
                "kf_id": BROAD_KF_ID,
                "name": BROAD_SC_CENTER,
                "external_id": BROAD_SC_CENTER,
                "endpoint": "sequencing-centers"
            }
        ]
        for p in payloads:
            endpoint = p.pop("endpoint", None)
            url = f"{self.dataservice_url}/{endpoint}"
            self.logger.info(f"Creating {url}")
            try:
                resp = self.session.post(url, json=p)
                resp.raise_for_status()
            except requests.exceptions.HTTPError:
                ok = resp.status_code == 400 and "already exists" in resp.text
                if not ok:
                    raise

    def run_ingest_pipeline(self):
        """
        Setup and run the ingest pipeline to ingest study data files into
        Data Service
        """
        # Initialize pipeline - use default settings (KF Data Service)
        self.ingest_pipeline = DataIngestPipeline(
            self.ingest_package_dir,
            self.ingest_settings,
        )
        # Set ingest package study
        self.ingest_pipeline.data_ingest_config.study = self.study_id

        # Run ingest
        self.ingest_pipeline.run()

    def _create_bio_manifest(self):
        """
        Create a tabular data file representing a clinical/bio manifest

        Includes _total_specimen_ # of participants, 1 specimen per
        participant, and 2 families. Participants are divided evenly between
        the 2 families.

        The default configuration would result in:

            - 2 families
            - 10 participants
            - 10 biospecimens

        Each entity has the minimal attributes needed to sucessfully ingest
        into the Data Service.

        Return a DataFrame with the data
        """
        # Create data file
        _range = range(self.total_specimens)
        bio_dict = {
            "sample_id": [f"SM-{i}" for i in _range],
            "participant_id": [f"CARE-{i}" for i in _range],
            "gender": [ra.choice(("Female", "Male")) for _ in _range],
            "volume": [100] * self.total_specimens,
            "concentration": [30] * self.total_specimens,
            "family_id": ["FA-1" if (i % 2) == 0 else "FA-2" for i in _range],
            "tissue_type": [ra.choice(("Blood", "Saliva")) for _ in _range],
        }
        # Insert KF IDs
        for key in ["participant", "biospecimen"]:
            prefix = self.id_prefixes[key]
            kf_ids = [kf_id_generator(prefix) for _ in _range]
            bio_dict[f"kf_id_{key}"] = kf_ids

        prefix = self.id_prefixes["family"]
        choices = {eid: kf_id_generator(prefix) for eid in ["FA-1", "FA-2"]}
        bio_dict["kf_id_family"] = [choices[fid] for fid in
                                    bio_dict["family_id"]]
        df = pd.DataFrame(bio_dict)
        return df

    def _create_sequencing_manifest(self):
        """
        Create a sequencing experiment and genomic file manifest with source
        (unharmonized) and harmonized file records. This is also used to 
        create the S3 object manifests and BIX genomic workflow manifests.

        Each record has minimal attributes needed to successfully create
        genomic files in Data Service. Includes N source genomic file records
        per specimen, where N is the number of file extensions in
        SOURCE_GF_EXTS, and 1 harmonized genomic file with ext HARM_GF_EXT
        per specimen.

        The default configuration would result in:

            - 30 (10 .cram, 10 .crai, 10 .cram.md5) source genomic file records
            - 10 (g.vcf.gz) harmonized genomic file records

        Return a manifest of the files created
        """
        def s3_path(filename, harmonized=False):
            """ Create an S3 object path for a genomic file """
            prefix = 'harmonized' if harmonized else 'source'
            return (
                f"s3://{self.study_bucket}/{prefix}/genomic-files/{filename}"
            )

        prefix = self.id_prefixes["genomic_file"]
        rows = []
        for gi in range(self.total_specimens):
            # Harmonized
            row_dict = {
                "sample_id": f"SM-{gi}",
                "experiment_strategy": ra.choice(["WGS", "WXS"]),
                "harmonized_path": s3_path(
                    f"genomic-file-{gi}{HARM_GF_EXT}", harmonized=True
                ),
            }
            # Unharmonized
            for ei, ext in enumerate(SOURCE_GF_EXTS):
                row_dict = row_dict.copy()
                row_dict["kf_id_genomic_file"] = kf_id_generator(prefix)
                row_dict["project_id"] = f"SE-{row_dict['sample_id']}"
                row_dict["source_path"] = s3_path(
                    f"genomic-file-{gi}-{ei}{ext}", harmonized=False
                )
                rows.append(row_dict)

        df = pd.DataFrame(rows)

        return df

    def _create_s3_gf_manifest(self, harmonized=False):
        """
        Create S3 object manifest for genomic files
        """
        if harmonized:
            filepath_col = "harmonized_path"
        else:
            filepath_col = "source_path"

        gf_df = self.dataframes["sequencing_manifest.tsv"]
        df = gf_df.drop_duplicates(filepath_col)[[filepath_col]]
        df["Bucket"] = self.study_bucket
        df["Key"] = df[filepath_col].map(
            lambda fp: fp.split(self.study_bucket)[-1].lstrip("/")
            .split(self.data_dir)[-1]
        )
        df["Filepath"] = df[filepath_col]
        df["Size"] = ra.randint(10 ** 6, 100 ** 6)
        df["ETag"] = str(uuid.uuid4()).replace("-", "")
        df["StorageClass"] = "STANDARD"
        df["LastModified"] = str(datetime.datetime.utcnow())

        return df

    def _create_bix_gwo_manifest(self):
        """
        Create BIX genomic workflow output manifest
        """
        def create_hex(n):
            """ Return a random hex number of length n. """
            return "".join(
                [ra.choice(string.hexdigits).lower() for _ in range(n)]
            )

        def data_type(filepath):
            """ Return genomic file data type based on file ext """
            if filepath.endswith(HARM_GF_EXT):
                dt = "gVCF"
            else:
                dt = None
            return dt

        def workflow_type(data_type):
            """ Return genomic workflow type based on data type """
            if data_type in {"gVCF"}:
                wt = "alignment"
            else:
                wt = None
            return wt

        # Merge all dfs
        bio_df = self.dataframes["bio_manifest.tsv"]
        gf_df = self.dataframes["sequencing_manifest.tsv"]
        df = pandas_utils.merge_wo_duplicates(bio_df, gf_df, on="sample_id")
        # Add additional columns
        df["Data Type"] = df["harmonized_path"].map(lambda fp: data_type(fp))
        df["Workflow Type"] = df["Data Type"].map(lambda dt: workflow_type(dt))
        df["Cavatica ID"] = create_hex(25)
        df["Cavatica Task ID"] = (
            "-".join([create_hex(i) for i in [8, 4, 4, 4, 12]])
        )
        # Rename columns
        col_map = {
            "kf_id_participant": "KF Participant ID",
            "kf_id_biospecimen": "KF Biospecimen ID",
            "kf_id_family": "KF Family ID",
            "harmonized_path": "Filepath",
            "source_path": "Source Read",
        }
        df = df[
            list(col_map.keys()) +
            ["Data Type", "Workflow Type", "Cavatica ID", "Cavatica Task ID"]
        ].rename(columns=col_map)

        return df

    def _assert_load(self):
        """
        Ensure all kf ids in the data files got loaded into Data Service
        """
        # Extract kf ids
        bio_df = self.dataframes["bio_manifest.tsv"]
        gf_df = self.dataframes["sequencing_manifest.tsv"]
        kfids = {
            "families": bio_df[["kf_id_family"]],
            "participants": bio_df[["kf_id_participant"]],
            "biospecimens": bio_df[["kf_id_biospecimen"]],
            "genomic-files": gf_df[["kf_id_genomic_file"]],
        }
        for endpoint, df in kfids.items():
            self.logger.info(f"Check all {endpoint} were loaded")
            # Check kf ids
            kfids = df[df.columns[0]].drop_duplicates().values.tolist()
            base_url = f"{self.dataservice_url}/{endpoint}"
            for kfid in kfids:
                url = f"{base_url}/{kfid}"
                self.logger.info(f"Checking {url}")
                resp = requests.get(url)
                resp.raise_for_status()

            # Check exact count
            params = {"study_id": self.study_id}
            count = len(kfids)
            if endpoint == "genomic-files":
                params["harmonized"] = False
            resp = requests.get(base_url, params=params)
            total = resp.json()["total"]
            assert total == count, (
                f"{endpoint} expected count {count} != {total} found"
            )


def delete_entities(dataservice_url, study_id=None, logger=None):
    """
    Delete entities (all or within single study) in Data Service

    NOTE - This should probably be moved to the kf-utils-python repo
    https://github.com/kids-first/kf-utils-python, however until CI/testing
    is implemented (See issue #21) we need to keep it here where it can
    actually be tested against a live Data Service.

    :param study_id: If provided, entities linked to this study id will
    be deleted, otherwise all entities in Data Service will be deleted
    :type study_id: bool
    """
    if not logger:
        logger = logging.getLogger("DeleteDataserviceEntities")

    session = Session()

    def _delete_kfids(endpoint, kfids):
        """
        Delete each KF ID in _kfids_ at _endpoint_
        """
        for i, kf_id in enumerate(kfids):
            url = f"{dataservice_url}/{endpoint}/{kf_id}"
            logger.info(f"Deleting {url}")
            try:
                resp = session.delete(url)
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.error(
                    f"Failed to delete {url}, status: {resp.status_code}. "
                    f"\nCaused by {str(e)}"
                )

    study_phrase = (
        f"study {study_id}" if study_id else "all studies"
    )
    logger.info(
        f"Deleting {study_phrase} from {dataservice_url}"
    )

    # Delete all entities except study (has to be handled differently)
    for endpoint in ENDPOINTS[:-1]:
        if not study_id:
            params = {}
        else:
            params = {"study_id": study_id}

        kfids = yield_kfids(dataservice_url, endpoint, params)
        _delete_kfids(endpoint, kfids)

    # Delete study(ies)
    endpoint = ENDPOINTS[-1]
    if not study_id:
        kfids = yield_kfids(dataservice_url, endpoint, {})
    else:
        kfids = [study_id]
    _delete_kfids(endpoint, kfids)
