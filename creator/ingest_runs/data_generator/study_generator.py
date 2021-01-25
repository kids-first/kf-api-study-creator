"""
A fake KF study generator that generates realistic studies
Used to setup unit tests for ingest runs and related functionality

1. Create (or read previously created) study files
- Create a biological TSV file with minimal family, participant, specimen data
- Create source and harmonized genomic files
- Upload genomic files to study bucket on S3
- Create S3 object manifest for source genomic files
- Create the BIX Genomic Workflow Output Manifest

2. Ingest study files into the KF Data Service (except the BIX manifest)
"""
import os
import logging
import random as ra
import string
from pprint import pprint

import boto3
from botocore.exceptions import ClientError
import requests
import pandas as pd

from kf_lib_data_ingest.common.io import read_df
from kf_lib_data_ingest.common import pandas_utils
from kf_lib_data_ingest.app import settings as ingest_settings
from kf_lib_data_ingest.etl.ingest_pipeline import DataIngestPipeline

from creator.fields import kf_id_generator
from creator.ingest_runs.utils import fetch_s3_obj_info

# For data generation
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data_generator", "ingest_package", "data")
INGEST_PKG_DIR = os.path.join(ROOT_DIR, "data_generator", "ingest_package")

# Connections
DATASERVICE_URL = "http://localhost:5000"
AWS_PROFILE = os.environ.get('AWS_PROFILE', "saml")
TEMP_STUDY_BUCKET = "kf-api-study-creator-ingest-test"
boto3.setup_default_session(profile_name=AWS_PROFILE)


class StudyGenerator(object):
    def __init__(
        self,
        data_dir=DATA_DIR,
        ingest_package_dir=INGEST_PKG_DIR,
        study_id="SD_ME0WME0W",
        sequencing_centers=None,
        total_specimens=10,
    ):
        self.data_dir = data_dir
        self.study_id = study_id
        if not sequencing_centers:
            sequencing_centers = [
                {
                    "kf_id": "SC_DGDDQVYR",
                    "name": "Broad Institute",
                }
            ]
        self.sequencing_centers = sequencing_centers
        self.total_specimens = total_specimens
        self.source_gf_extensions = [".cram", ".crai", ".cram.md5"]
        self.logger = logging.getLogger(type(self).__name__)

        # Initialize ingest - use default settings (KF Data Service)
        self.ingest_pipeline = DataIngestPipeline(
            ingest_package_dir,
            ingest_settings.load().TARGET_API_CONFIG,
        )
        # KF ID Prefixes
        self.id_prefixes = {
            "family": "FM",
            "participant": "PT",
            "biospecimen": "BS",
            "genomic_file": "GF",
        }

    @property
    def study_bucket(self):
        """ Return study bucket from study KF ID """
        return (
            f"kf-study-us-east-1-dev-"
            f"{self.study_id.lower().replace('_', '-')}"
        )

    def ingest_study(self, initialize=False, create_files=False):
        """
        Entrypoint. Ingest study data files into Data Service

        :param initialize: Create the study and sequencing centers in the data
        service
        :type initialize: bool
        :param create_files: Create the study data files if True, otherwise
        read them from disk
        :type create_files: bool
        """

        # Create study, sequencing center info
        if initialize:
            self._initialize_study()

        # Create new or read in existing study data files
        kf_ids = self.generate_files(create=create_files)

        # Ingest study data files into Data Service
        self.ingest_pipeline.run()

        # Ensure all kf_ids were loaded
        for endpoint, kfids in kf_ids.items():
            self._assert_load(endpoint, kfids)

    def generate_files(self, create=False):
        """
        Generate clinical and genomic data files for a test study

        :param create: Create new data files or read existing files
        :type create: bool
        """
        ra.seed(0)
        self.logger.info(
            f"Creating clinical and genomic files for {self.study_id}"
        )

        # Create clinical and genomic data files
        bio_df = self._create_bio_manifest(create=create)
        gf_df = self._create_gfs(create=create)

        # Upload unharmonized and harmonized gfs to S3
        if create:
            self._upload_gfs_to_s3()

        # Write S3 object manifests for genomic files to disk
        s3_df = self._create_gf_s3_manifests(create=create)

        # Create BIX GWO Manifest and upload to S3
        if create:
            dfs = bio_df, gf_df, s3_df
        else:
            dfs = None
        gwo_df = self._create_bix_gwo_manifest(dfs=dfs)

        # Return kf ids for later validation
        return {
            "participants": bio_df["kf_id_participant"].unique(),
            "biospecimens": bio_df["kf_id_biospecimen"].unique(),
            "families": bio_df["kf_id_family"].unique(),
            "genomic-files": gf_df["kf_id_genomic_file"].unique(),
        }

    def _initialize_study(self):
        """
        Create study, sequencing-center in Data Service
        """
        self.logger.info(
            f"Initializing study {self.study_id} in "
            f"Data Service {DATASERVICE_URL}"
        )
        payloads = [
            {
                "kf_id": self.study_id,
                "name": self.study_id,
                "external_id": self.study_id,
                "endpoint": "studies"
            },
        ]
        for sc in self.sequencing_centers:
            payloads.append(
                {
                    "kf_id": sc["kf_id"],
                    "name": sc["name"],
                    "external_id": sc["name"],
                    "endpoint": "sequencing-centers"
                }
            )
        for p in payloads:
            endpoint = p.pop("endpoint", None)
            url = f"{DATASERVICE_URL}/{endpoint}"
            self.logger.info(f"Creating {url}")
            try:
                resp = requests.post(url, json=p)
                resp.raise_for_status()
            except requests.exceptions.HTTPError:
                ok = resp.status_code == 400 and "already exists" in resp.text
                if not ok:
                    raise

    def _create_bio_manifest(self, create=False):
        """
        Create a tabular data file representing a Biospecimen manifest. This
        just includes the necessary attributes to ingest Biospecimen entities.
        N rows are generated, one for each Biospecimen. The number needed is
        up to the user. The simplest solution is to have one per participant.
        """
        verb = "Creating" if create else "Reading"
        n = self.total_specimens
        self.logger.info(
            f"{verb} bio manifest with {n} participants, "
            "each with 1 specimen"
        )
        fp = os.path.join(self.data_dir, 'bio_manifest.tsv')
        if not create:
            return read_df(fp)

        _range = range(n)
        bio_dict = {
            "sample_id": [f"SM-{i}" for i in _range],
            "participant_id": [f"CARE-{i}" for i in _range],
            "gender": [ra.choice(("Female", "Male")) for _ in _range],
            "volume": [100] * n,
            "concentration": [30] * n,
            "family_id": [ra.choice(("FA-1", "FA-2")) for _ in _range],
            "tissue_type": [ra.choice(("Blood", "Saliva")) for _ in _range],
        }
        id_gen = kf_id_generator
        for key in ["participant", "biospecimen", "family"]:
            if key == "family":
                fids = [id_gen(self.id_prefixes[key]) for _ in range(2)]
                kf_ids = [
                    fids[0] if fid == "FA-1" else fids[1]
                    for fid in bio_dict['family_id']
                ]
            else:
                kf_ids = [id_gen(self.id_prefixes[key]) for _ in _range]
            bio_dict[f"kf_id_{key}"] = kf_ids

        os.makedirs(self.data_dir, exist_ok=True)
        df = pd.DataFrame(bio_dict)
        df.to_csv(fp, sep='\t', index=False)

        self.logger.info(f"Wrote bio manifest to {fp}")

        return df

    def _create_gfs(self, create=False):
        """
        Create realistic fake genomic files (unharmonized and harmonized)
        and return manifest with an inventory of created files

        Create 3 unharmonized genomic files for each specimen. Each file will
        have a different extension: .crai, .cram, and .md5 to better simulate
        a real study. Each of these 3 * total files will simply be a text file
        with a randomly-generated string of text. These files will then need
        to be uploaded to their respective S3 buckets.

        Create 1 harmonized genomic file (g.vcf.gz) per specimen

        Return a manifest of the files created
        """
        n = self.total_specimens
        f = len(self.source_gf_extensions)
        verb = "Creating" if create else "Reading"
        self.logger.info(
            f"{verb} {f} source files per specimen and 1 "
            "harmonized files per source file: "
            f"{n*3 + n} total genomic files"
        )
        manifest_fp = os.path.join(self.data_dir, 'gf_manifest.tsv')
        if not create:
            return read_df(manifest_fp)

        # Create data dir paths
        ugf_dir = os.path.join(self.data_dir, 'source', 'genomic-files')
        hgf_dir = os.path.join(self.data_dir, 'harmonized', "genomic-files")

        def make_file(i, extension, harmonized=False):
            """ Create fake genomic file and write to disk """
            # Generate random text of random length
            file_text = "".join(
                ra.choice(string.ascii_letters + string.digits)
                for _ in range(ra.randint(10, 1000))
            )
            # Determine unharmonized / harmonized dir
            file_dir = hgf_dir if harmonized else ugf_dir
            os.makedirs(file_dir, exist_ok=True)
            filepath = os.path.join(file_dir, f"genomic-file-{i}{extension}")
            with open(filepath, "w") as f:
                f.write(file_text)

            self.logger.info(f"Wrote {filepath} to disk")

            return filepath

        def s3_path(filename, harmonized=False):
            """ Create an S3 object path for a genomic file """
            prefix = 'harmonized' if harmonized else 'source'
            return (
                f"s3://{self.study_bucket}/{prefix}/"
                f"genomic-files/{filename}"
            )

        # Write files and create genomic files manifest
        id_gen = kf_id_generator
        prefix = self.id_prefixes["genomic_file"]
        rows = []
        for gi in range(self.total_specimens):
            # Harmonized
            ext = ".g.vcf.gz"
            h = True
            fp = make_file(gi, ext, harmonized=h)
            row_dict = {
                "sample_id": f"SM-{gi}",
                "data_type": "WGS",
                "filepath": s3_path(os.path.split(fp)[-1], harmonized=h),
            }
            # Unharmonized
            for ei, extension in enumerate(self.source_gf_extensions):
                h = False
                fp = make_file(f'{gi}-{ei}', extension, harmonized=h)
                row_dict = row_dict.copy()
                # Use fixed ids for source gfs
                row_dict["kf_id_genomic_file"] = id_gen(prefix)
                row_dict["project_id"] = f"SE-{row_dict['sample_id']}"
                row_dict["source_read"] = s3_path(
                    os.path.split(fp)[-1], harmonized=h
                )
                rows.append(row_dict)

        df = pd.DataFrame(rows)
        df.to_csv(manifest_fp, sep='\t', index=False)
        self.logger.info(f"Wrote {manifest_fp}")

        return df

    def _upload_gfs_to_s3(self):
        """
        Upload gfs to S3 study bucket
        """
        self.logger.info(
            f"Uploading genomic files in {self.data_dir} to S3 bucket "
            f"{self.study_bucket}"
        )

        s3_client = boto3.client('s3')
        gf_manifest = read_df(os.path.join(self.data_dir, "gf_manifest.tsv"))

        s3_paths = sorted(
            list(gf_manifest["filepath"].drop_duplicates().values) +
            list(gf_manifest["source_read"].drop_duplicates().values)
        )
        for s3_path in s3_paths:
            suffix = (
                s3_path.split(f"s3://{self.study_bucket}")[-1].lstrip("/")
            )
            fp = os.path.join(self.data_dir, suffix)
            try:
                s3_client.upload_file(fp, self.study_bucket, suffix)
            except ClientError as e:
                self.logger.error(e)
            self.logger.info(
                f"Uploaded {suffix} to {s3_path}"
            )

    def _create_gf_s3_manifests(self, create=False):
        """
        Generate S3 object manifests for unharmonized and harmonized
        genomic files
        """
        verb = "Creating" if create else "Reading"
        self.logger.info(
            f"{verb} S3 object manifest for genomic files in "
            f"s3://{self.study_bucket}"
        )
        fp = os.path.join(self.data_dir, 's3_gf_manifest.tsv')
        if not create:
            return read_df(fp)

        df = fetch_s3_obj_info(
            bucket_name=self.study_bucket,
            search_prefixes=[
                "source/genomic-files/",
                "harmonized/genomic-files/"
            ],
        )

        # Filter out folders
        df = df[~df["Filename"].isnull()]

        df.to_csv(fp, sep="\t", index=False)
        self.logger.info(f"Wrote S3 manifest for genomic files: {fp}")

        return df

    def _create_bix_gwo_manifest(self, dfs=None):
        """
        Create BIX genomic workflow output manifest
        """
        create = dfs
        fp = os.path.join(self.data_dir, 'gwo_manifest.tsv')
        verb = "Creating" if create else "Reading"
        self.logger.info(
            f"{verb} bioinformatics genomic workflow output manifest {fp}"
        )
        if not create:
            return read_df(fp)

        def create_hex(n):
            """
            Return a random hex number of length n.
            """
            return "".join(
                [ra.choice(string.hexdigits).lower() for _ in range(n)]
            )

        def data_type(row):
            if row["filepath"].endswith("g.vcf.gz"):
                dt = "gVCF"
            else:
                dt = None
            return dt

        def workflow_type(row):
            if row["Data Type"] in {"gVCF"}:
                wt = "alignment"
            else:
                wt = None
            return wt

        # Merge all dfs
        bio_df, gf_df, s3_df = dfs
        s3_df.columns = [c.lower() for c in s3_df.columns]
        df = pandas_utils.merge_wo_duplicates(bio_df, gf_df, on="sample_id")
        df = pandas_utils.merge_wo_duplicates(df, s3_df, on="filepath")
        # Add additional columns
        df["Data Type"] = df.apply(lambda row: data_type(row), axis=1)
        df["Workflow Type"] = df.apply(lambda row: workflow_type(row), axis=1)
        df["Cavatica ID"] = create_hex(25)
        df["Cavatica Task ID"] = (
            "-".join([create_hex(i) for i in [8, 4, 4, 4, 12]])
        )
        # Rename columns
        col_map = {
            "kf_id_participant": "KF Participant ID",
            "kf_id_biospecimen": "KF Biospecimen ID",
            "kf_id_family": "KF Family ID",
            "filepath": "Filepath",
            "source_read": "Source Read",
        }
        df = df[
            list(col_map.keys()) +
            ["Data Type", "Workflow Type", "Cavatica ID", "Cavatica Task ID"]
        ].rename(columns=col_map)

        df.to_csv(fp, sep="\t", index=False)
        self.logger.info(f"Wrote {fp}")

        return df

    def _assert_load(self, endpoint, kf_ids):
        """
        Ensure all kf ids exist and entity count in Data Service
        matches len(kf_ids)
        """
        self.logger.info(f"Check all {endpoint} were loaded")

        base_url = f"{DATASERVICE_URL}/{endpoint}"
        for kfid in kf_ids:
            # Check kf ids
            url = f"{base_url}/{kfid}"
            self.logger.info(f"Checking {url}")
            resp = requests.get(url)
            resp.raise_for_status()

        # Check exact count
        count = len(kf_ids)
        if endpoint == "genomic-files":
            params = {"harmonized": False}
        else:
            params = None
        resp = requests.get(base_url, params=params)
        total = resp.json()["total"]
        assert total == count, (
            f"{endpoint} expected count {count} != {total} found"
        )


if __name__ == '__main__':
    sg = StudyGenerator()
    sg.ingest_study(initialize=False, create_files=False)
    # sg.generate_files(create=True)
