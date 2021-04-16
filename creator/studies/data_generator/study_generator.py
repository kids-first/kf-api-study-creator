"""
Generates fake but realistic Dataservice studies
Used to setup unit tests for ingest runs and related functionality

Study generator ingest consists of the following steps:

1. (Optional) Delete all previously generated data on disk, then
   delete study in Dataservice

2. Create a study ingest package at
<StudyGenerator.working_dir>/<StudyGenerator.study_id>_ingest_package

3. Read existing or create new study data files representing a minimal study
    - bio_manifest.tsv
    - sequencing_manifest.tsv
    - s3_source_gf_manifest.tsv
    - s3_harmonized_gf_manifest.tsv
    - gwo_manifest.tsv

4. Load study and sequencing center in Dataservice

5. Ingest study data files into Dataservice using ingest library
    - Uses the KF ingest lib to do this

Upon completion of ingest, the following entities will  be in Dataservice:
    - sequencing_center
    - study
    - family
    - participant
    - biospecimen
    - genomic_file (only harmonized=False)
    - biospecimen_genomic_file
    - sequencing_experiment
    - sequencing_experiment_genomic_file

"""
import os
from collections import defaultdict
import datetime
import logging
import shutil
import string
import uuid
import random as ra
from pprint import pformat, pprint

from django.conf import settings

import requests
import pandas as pd
from d3b_utils.requests_retry import Session
from kf_utils.dataservice.delete import delete_entities
from kf_lib_data_ingest.common.io import read_df
from kf_lib_data_ingest.common import pandas_utils
from kf_lib_data_ingest.app import settings as ingest_settings
from kf_lib_data_ingest.etl.ingest_pipeline import DataIngestPipeline

from creator.fields import kf_id_generator

# For data generation
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
INGEST_PKG_TEMPLATE = os.path.join(ROOT_DIR, "ingest_package")
DEFAULT_STUDY_ID = "SD_ME0WME0W"
BROAD_SC_CENTER = "Broad Institute"
BROAD_KF_ID = "SC_DGDDQVYR"
SOURCE_GF_EXTS = (".cram", ".crai", ".cram.md5")
HARM_GF_EXT = ".g.vcf.gz"
DEFAULT_SPECIMENS = 10
ENTITY_ENDPOINTS = {
    "read_group": "read-groups",
    "read_group_genomic_file": "read-group-genomic-files",
    "sequencing_experiment": "sequencing-experiments",
    "sequencing_experiment_genomic_file": "sequencing-experiment-genomic-files",  # noqa
    "genomic_file": "genomic-files",
    "biospecimen_genomic_file": "biospecimen-genomic-files",
    "biospecimen": "biospecimens",
    "outcome": "outcomes",
    "phenotype": "phenotypes",
    "diagnosis": "diagnoses",
    "participant": "participants",
    "family_relationship": "family-relationships",
    "family": "families",
    "study": "studies",
}

logger = logging.getLogger(__name__)


class StudyGenerator(object):
    def __init__(
        self,
        working_dir: str = None,
        dataservice_url: str = None,
        study_id: str = DEFAULT_STUDY_ID,
        total_specimens: int = DEFAULT_SPECIMENS,
    ):
        """
        Constructor

        :param working_dir: the directory where the study ingest package along
        with data files will be written. Defaults to current working directory
        :param study_id: Kids First study_id to use when creating the study in
        Dataservice
        :param dataservice_url: URL of Dataservice where study will be loaded
        :param total_specimens: See _generate_files for details on how this
        is used.
        """
        self.dataservice_url = dataservice_url or settings.DATASERVICE_URL
        self.study_id = study_id
        self.total_specimens = total_specimens

        # Setup directory paths
        if not working_dir:
            self.working_dir = os.getcwd()
        else:
            self.working_dir = os.path.abspath(working_dir)
        self.ingest_package_dir = os.path.join(
            self.working_dir, f"{self.study_id}_ingest_package"
        )
        self.data_dir = os.path.join(self.ingest_package_dir, "data")

        # For loading data into Dataservice
        self.id_prefixes = {
            "family": "FM",
            "participant": "PT",
            "biospecimen": "BS",
            "genomic_file": "GF",
        }
        self._df_creators = {
            "bio_manifest.tsv": self._create_bio_manifest,
            "sequencing_manifest.tsv": self._create_sequencing_manifest,
            "s3_source_gf_manifest.tsv": self._create_s3_source_gf_manifest,
            "s3_harmonized_gf_manifest.tsv": self._create_s3_harmonized_gf_manifest,  # noqa
            "gwo_manifest.tsv": self._create_bix_gwo_manifest,
        }
        self.dataframes = {}
        self.session = None
        self.ingest_pipeline = None
        self.dataservice_payloads = defaultdict(dict)

    @property
    def study_bucket(self) -> str:
        """ Return study bucket from study KF ID """
        return (
            f"kf-study-us-east-1-dev-{self.study_id.lower().replace('_', '-')}"
        )

    def ingest_study(
        self,
        clean: bool = True,
        random_seed: bool = True,
        verify_counts: bool = True,
        **ingest_kwargs
    ) -> None:
        """
        Entrypoint. Ingest study data into Dataservice:

        OPTIONAL - Cleanup before doing anything else:

        1. Delete study data in Dataservice
        2. Delete study ingest package (includes data files)

        See _clean_ for details on clean up operations

        1. Create a study ingest package in _working_dir_ named
        <study_id>_ingest_package
        2. Read or create new clinical data file in ingest package
        3. Read or create new genomic data files in ingest package
        4. Create study and sequencing center in Dataservice
        5. Ingest study data files into Dataservice
        6. OPTIONAL - Verify that all KF IDs in the generated files were loaded
        into the Dataservice and that the total entity counts = number of
        KF IDs

        See _generate_files_ for details on data files

        :param clean: Whether or not to clean before running ingest. See
        _clean_ for details
        :param random_seed: Whether to use a random seed or same seed when
        generating random values (e.g. KF IDs)
        :param verify_counts: Whether to verify that all KF IDs in the
        generated data files got loaded into Dataservice. Or if ingest was
        run with dry_run=True, then check the payloads that would be sent to
        Dataservice
        :param ingest_kwargs: Keyword arguments to forward to the constructor
        of the ingest pipeline, called in run_ingest_pipeline
        """
        dry_run = ingest_kwargs.get("dry_run")

        if not random_seed:
            ra.seed(0)

        # Cleanup all previously written data and data loaded into Dataservice
        if clean:
            self.clean(dry_run=dry_run)

        # Create study data files
        self.generate_files()

        # Ingest study, seq center, and study data files into Dataservice
        self.run_ingest_pipeline(**ingest_kwargs)

        # Ensure all kf_ids were loaded and entity counts are valid
        if verify_counts:
            self._verify_counts(dry_run=dry_run)

    def clean(self, dry_run: bool = False, all_studies: bool = False) -> None:
        """
        Clean up data before ingestion begins

        1. Delete study data in Dataservice (if not a dry run ingest)
        2. Delete existing ingest package with data files

        :param all_studies: Whether to delete all studies' data in
        Dataservice or just the entities linked to StudyGenerator.study_id
        :param dry_run: Whether its a dry run ingest, and therefore does not
        require deleting study data from dataservice
        """
        logger.info("Clean up before study generation begins")

        # Delete entities in Dataservice
        if not dry_run:
            study_ids = None if all_studies else [self.study_id]
            delete_entities(self.dataservice_url, study_ids=study_ids)

        # Delete existing data files
        logger.info(f"Deleting files in {self.ingest_package_dir}")
        shutil.rmtree(self.ingest_package_dir, ignore_errors=True)

    def generate_files(self) -> None:
        """
        Generate data files for a test study which have columns that conform 
        to the file types in creator.analyses.file_types
        Read files into DataFrames if they exist, otherwise create them:

        1. bio_manifest.tsv
        2. sequencing_manifest.tsv
        3. s3_source_gf_manifest.tsv
        4. s3_harmonized_gf_manifest.tsv
        5. gwo_manifest.tsv

        Files are written to:
        <StudyGenerator.working_dir>/<StudyGenerator.study_id>_ingest_package/data # noqa
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
        logger.info(
            f"Creating clinical and genomic files for {self.study_id}. "
            f"Entities:\n{pformat(self.expected_counts)}"
        )

        # Try read from disk
        fps = [os.path.join(self.data_dir, fn) for fn in self._df_creators]
        read_existing = all([os.path.exists(fp) for fp in fps])
        if read_existing:
            for fp in fps:
                logger.info(f"Reading {fp}")
                df = read_df(fp)
                self.dataframes[os.path.split(fp)[-1]] = df
            return

        # Create data
        self._create_dfs()

        # Write data
        self._write_dfs()

    def _create_dfs(self) -> None:
        """
        Creates all DataFrames
        """
        for fn, func in self._df_creators.items():
            logger.info(f"Creating {fn.split('.')[0]}")
            if fn in self.dataframes:
                continue
            self.dataframes[fn] = pd.DataFrame(func())

    def _write_dfs(self) -> None:
        """
        Write StudyGenerator's DataFrames to disk
        """
        # Create ingest package and data dir if it doesn't exist
        if not os.path.exists(self.ingest_package_dir):
            shutil.copytree(
                INGEST_PKG_TEMPLATE, self.ingest_package_dir
            )
            os.makedirs(self.data_dir, exist_ok=True)

        # Write to disk
        for fn in self._df_creators:
            fp = os.path.join(self.data_dir, fn)
            logger.info(f"Writing {fp}")
            self.dataframes[fn].to_csv(fp, sep='\t', index=False)

    def initialize_study(self) -> None:
        """
        Create study, sequencing_center entities in Dataservice
        """
        if not self.session:
            self.session = Session()

        logger.info(
            f"Initializing study {self.study_id} in "
            f"Dataservice {self.dataservice_url}"
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
            logger.info(f"Creating {url}")
            resp = self.session.post(url, json=p)
            resp.raise_for_status()

    def run_ingest_pipeline(self, **ingest_kwargs) -> None:
        """
        Setup and run the ingest pipeline to ingest study data files into
        Dataservice

        :param ingest_kwargs: Keyword arguments to forward to the constructor
        of the ingest pipeline
        """

        dry_run = ingest_kwargs.get("dry_run")
        if not dry_run:
            # Load study, sequencing center into Dataservice
            self.initialize_study()

        # Initialize pipeline - use default settings (KF Dataservice)
        self.ingest_pipeline = DataIngestPipeline(
            self.ingest_package_dir,
            ingest_settings.load().TARGET_API_CONFIG,
            **ingest_kwargs,
        )
        # Set study_id in ingest package
        self.ingest_pipeline.data_ingest_config.project = self.study_id

        # Run ingest
        self.ingest_pipeline.run()

        # Provide easy access to the payloads that were sent to the Dataservice
        for payload in (
            self.ingest_pipeline.stages.get("LoadStage").sent_messages
        ):
            etype = payload["type"]
            kf_id = payload["body"]["kf_id"]
            self.dataservice_payloads[etype][kf_id] = payload["body"]

        self.cache = getattr(
            self.ingest_pipeline.stages.get("LoadStage"),
            "uid_cache",
            None
        )

    def _create_bio_manifest(self) -> pd.DataFrame:
        """
        Create bio data for _total_specimen_ # of participants and specimens

        The default configuration would result in:

            - 2 families
            - 10 participants
            - 10 specimens
            - 10 conditions
            - 10 observations
            - 10 outcomes

        Each entity has the minimal attributes needed to sucessfully ingest
        into the Dataservice.

        Return a DataFrame with the data
        """
        # Create data file
        _range = range(self.total_specimens)

        pids = [f"PT-{i}" for i in _range]
        mids = ["PT-M1" if (i % 2) == 0 else "PT-M2" for i in _range]

        bio_dict = {
            "KF ID Study": [self.study_id for i in _range],

            # --- PDA: Participant Demographics --- #
            "Family ID": ["FA-1" if (i % 2) == 0 else "FA-2" for i in _range],
            "Participant ID": pids,
            "dbGaP Consent Code": ["GRU" for i in _range],
            "Gender Identity": [
                ra.choice(["Male", "Female"]) for i in _range
            ],
            "Clinical Sex": [
                ra.choice(["Male", "Female"]) for i in _range
            ],
            "Race": [
                ra.choice([
                    "White",
                    "American Indian or Alaska Native",
                    "Black or African American",
                    "Asian",
                    "Native Hawaiian or Other Pacific Islander",
                    "More Than One Race",
                ]) for i in _range
            ],
            "Ethnicity": [
                ra.choice(["Hispanic or Latino", "Not Hispanic or Latino"])
                for i in _range
            ],
            "Age at Study Enrollment Value": [
                ra.randint(300, 1000) for i in _range
            ],
            "Age at Study Enrollment Units": ["days" for i in _range],
            "Affected Status": [ra.choice([True, False]) for i in _range],
            "Species": [
                ra.choice(['Homo Sapiens', 'Canis lupus familiaris'])
                for i in _range
            ],

            # --- PTO: Participant Outcomes --- #
            "Age at Status Value": [
                ra.randint(300, 1000) for i in _range
            ],
            "Age at Status Units": ["days" for i in _range],
            "Vital Status": [ra.choice(["Alive", "Deceased"]) for i in _range],
            "Disease Related": ["No" for i in _range],

            # --- PTD: Participant Diseases --- #
            "Age at Onset Value": [
                ra.randint(300, 1000) for i in _range
            ],
            "Age at Onset Units": ["days" for i in _range],
            "Age at Abatement Value": [
                ra.randint(300, 1000) for i in _range
            ],
            "Age at Abatement Units": ["days" for i in _range],
            "Verification Status": [
                ra.choice(["Positive", "Negative"]) for i in _range
            ],
            "Condition Name": ["cleft lip" for i in _range],
            "Condition MONDO Code": ["MONDO:0004747" for i in _range],
            "Body Site Name": ["lower lip" for i in _range],
            "Body Site UBERON Code": ["UBERON:0018150" for i in _range],
            "Spatial Descriptor": ["left" for i in _range],

            # --- PTP: Participant Phenotype --- #
            "Condition HPO Code": ["HP:0000175" for i in _range],

            # --- POB: General Observations --- #
            "Observation Name": ["cleft lip" for i in _range],
            "Observation Ontology Ontobee URI": [
                "http://hpo.org" for i in _range
            ],
            "Observation Code": ["HP:0000175" for i in _range],
            "Status": [ra.choice([True, False]) for i in _range],
            "Category": ["Structural Birth Defect" for i in _range],
            "Interpretation": [
                ra.choice(["Positive", "Negative"]) for i in _range
            ],
            "Age at Observation Value": [
                ra.randint(300, 1000) for i in _range
            ],
            "Age at Observation Units": ["days" for i in _range],

            # --- SAM: Participant Samples --- #
            "Sample ID": [f"SM-{i}" for i in _range],
            "Aliquot ID": [f"SM-{i}" for i in _range],
            "Tissue Type": ["Normal" for i in _range],
            "Composition": ["Tissue" for i in _range],
            "Age at Collection Value": [
                ra.randint(300, 1000) for i in _range
            ],
            "Age at Collection Units": ["days" for i in _range],
            "Consent Group": ["GRU" for i in _range],
            "Descriptor": ["Tissue Normal" for i in _range],
            "Method of Sample Procurement": ["Not Reported" for i in _range],
            "Volume": [ra.randint(0, 500) for i in _range],
            "Volume Units": ["ug" for i in _range],
            "Concentration": [ra.randint(1, 100) for i in _range],
            "Concentration Units": ["mg_per_ml" for i in _range],
            "Consent Short Name": ["General Research Use" for i in _range],

            # --- FTR: Family Trios --- #
            "Mother Participant ID": [
                "PT-M1" if (i % 2) == 0 else "PT-M2" for i in _range
            ],
            "Father Participant ID": [
                "PT-F1" if (i % 2) == 0 else "PT-F2" for i in _range
            ],
            "Proband": [ra.choice([True, False]) for i in _range],

            # --- FCM: Complex Family --- #
            "Source Participant ID": mids,
            "Target Participant ID": pids,
            "Family Relationship": ["Mother" for i in _range],

        }
        # Insert KF IDs
        for key in ["participant", "biospecimen"]:
            prefix = self.id_prefixes[key]
            kf_ids = [kf_id_generator(prefix) for _ in _range]
            bio_dict[f"KF ID {key.title()}"] = kf_ids

        prefix = self.id_prefixes["family"]
        choices = {eid: kf_id_generator(prefix) for eid in ["FA-1", "FA-2"]}
        bio_dict["KF ID Family"] = [
            choices[fid] for fid in bio_dict["Family ID"]
        ]

        df = pd.DataFrame(bio_dict)
        return df

    def _create_sequencing_manifest(self) -> pd.DataFrame:
        """
        Create a sequencing experiment and genomic file manifest with source
        (unharmonized) and harmonized file records. This is also used to
        create the S3 object manifests and BIX genomic workflow manifests.

        Each record has minimal attributes needed to successfully create
        genomic files in Dataservice. Includes N source genomic file records
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
                "Sample ID": f"SM-{gi}",
                "Aliquot ID": f"SM-{gi}",
                # Sequencing experiment info
                "Is Paired End": ra.choice([True, False]),
                "Analyte Type": ra.choice(["DNA", "RNA"]),
                "Sequencing Center": "Broad Institute",
                "Reference Genome": "GRCh38",
                "Experiment Strategy": ra.choice(["WGS", "WXS"]),
                "Experiment Name": f"SE-SM-{gi}",
                "Experiment Date": (
                    datetime.datetime.now().isoformat()
                ),
                "Instrument Model": "HiSeq 550",
                "Library Platform": "Illumina",
                "Library Name": f"SM-{gi}",
                "Library Strand": "Unstranded",
                "Library Selection": "PCR",
                "Library Prep": "polyA",
                "Max Insert Size": ra.randint(100, 500),
                "Mean Insert Size": ra.randint(100, 500),
                "Mean Depth": ra.randint(10, 400),
                "Total Reads": ra.randint(10, 1000),
                "Mean Read Length": ra.randint(50, 150),
                "Harmonized Path": s3_path(
                    f"genomic-file-{gi}{HARM_GF_EXT}", harmonized=True
                ),
                "KF ID Harmonized Genomic File": kf_id_generator(prefix)
            }
            # Unharmonized
            for ei, ext in enumerate(SOURCE_GF_EXTS):
                row_dict = row_dict.copy()
                row_dict["KF ID Source Genomic File"] = kf_id_generator(
                    prefix
                )
                row_dict["Source Sequencing Filepath"] = s3_path(
                    f"genomic-file-{gi}-{ei}{ext}", harmonized=False
                )

                rows.append(row_dict)

        df = pd.DataFrame(rows)

        return df

    def _create_s3_source_gf_manifest(self):
        """
        Create S3 object manifest for unharmonized genomic files
        """
        return self._create_s3_gf_manifest(harmonized=False)

    def _create_s3_harmonized_gf_manifest(self):
        """
        Create S3 object manifest for harmonized genomic files
        """
        return self._create_s3_gf_manifest(harmonized=True)

    def _create_s3_gf_manifest(self, harmonized: bool = False) -> pd.DataFrame:
        """
        Create S3 object manifest for genomic files

        :param harmonized: Aids in naming the filepath column based on whether
        the files are harmonized or not
        """
        filepath_col = (
            "Harmonized Path" if harmonized else "Source Sequencing Filepath"
        )

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

            return "gVCF" if filepath.endswith(HARM_GF_EXT) else None

        def workflow_type(data_type):
            """ Return genomic workflow type based on data type """

            return "alignment" if data_type in {"gVCF"} else None

        # Merge all dfs
        bio_df = self.dataframes["bio_manifest.tsv"]
        gf_df = self.dataframes["sequencing_manifest.tsv"]
        df = pandas_utils.merge_wo_duplicates(
            bio_df, gf_df, on="Sample ID"
        )
        # Add additional columns
        df["Data Type"] = df["Harmonized Path"].map(lambda fp: data_type(fp))
        df["Workflow Type"] = df["Data Type"].map(lambda dt: workflow_type(dt))
        df["Cavatica ID"] = create_hex(25)
        df["Cavatica Task ID"] = (
            "-".join([create_hex(i) for i in [8, 4, 4, 4, 12]])
        )
        # Rename columns
        col_map = {
            "KF ID Participant": "KF Participant ID",
            "KF ID Biospecimen": "KF Biospecimen ID",
            "KF ID Family": "KF Family ID",
            "Harmonized Path": "Filepath",
            "Source Sequencing Filepath": "Source Read",
        }
        df = df[
            list(col_map.keys()) +
            ["Data Type", "Workflow Type", "Cavatica ID", "Cavatica Task ID"]
        ].rename(columns=col_map)

        return df

    def _verify_counts(self, dry_run: bool = False) -> None:
        """
        Verify that Dataservice has been loaded with exactly the data that
        StudyGenerator generated. No more, no less.

        If in dry run mode, then use the ingest pipeline's to-be-sent payloads
        instead of querying the Dataservice to verify

        Check that all kf ids in the data files got loaded into Dataservice
        Check that total entity counts in Dataservice equal the number of
        KF IDs in the data files for each type of entity

        NOTE: For genomic files only the files with harmonized=False are
        checked since StudyGenerator does not ingest the harmonized files

        :param dry_run: Whether its a dry run ingest
        """
        def check_kfid(entity_type, kf_id):
            """
            Check the KF ID was loaded into Dataservice or if ingest was
            run in dry run mode, then check the KF ID is in the to-be loaded
            entities
            """
            msg = f"Verify {entity_type} {kf_id} failed!"
            if dry_run:
                assert entity_type in self.dataservice_payloads, msg
                assert kf_id in self.dataservice_payloads[entity_type], msg
            else:
                endpoint = ENTITY_ENDPOINTS.get(entity_type)
                url = f"{self.dataservice_url}/{endpoint}/{kf_id}"
                resp = requests.get(url)
                try:
                    resp.raise_for_status()
                except Exception as e:
                    raise AssertionError(f"{msg}. Caused by:\n {str(e)}")
            logger.info(f"Verified that {entity_type} {kf_id} was loaded")

        def check_count(entity_type, kfids):
            """
            Check that the entity counts in Dataservice equal number of
            KF IDs in the StudyGenerator data files for each type of entity
            """
            expected = len(kfids)
            params = {"study_id": self.study_id}
            if dry_run:
                total = len(self.dataservice_payloads.get(entity_type, {}))
            else:
                endpoint = ENTITY_ENDPOINTS.get(entity_type)
                if endpoint == "genomic-files":
                    params["harmonized"] = False
                url = f"{self.dataservice_url}/{endpoint}"
                resp = requests.get(url, params=params)
                total = resp.json()["total"]

            assert total == expected, (
                f"{entity_type} expected count {count} != {total} found"
            )
            logger.info(f"Verified {expected} {entity_type} were loaded")

        # Extract kf ids
        bio_df = self.dataframes["bio_manifest.tsv"]
        gf_df = self.dataframes["sequencing_manifest.tsv"]
        kfids = {
            "family": bio_df[["KF ID Family"]],
            "participant": bio_df[["KF ID Participant"]],
            "biospecimen": bio_df[["KF ID Biospecimen"]],
            "genomic_file": gf_df[["KF ID Source Genomic File"]],
        }
        for entity_type, df in kfids.items():
            logger.info(f"Check all {entity_type} were loaded")
            # Check kf ids
            kfids = df[df.columns[0]].drop_duplicates().values.tolist()
            for kfid in kfids:
                check_kfid(entity_type, kfid)
            # Check exact count
            check_count(entity_type, kfids)
