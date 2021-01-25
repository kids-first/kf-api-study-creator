from creator.ingest_runs import utils
import ast
import os
import logging
from pprint import pprint

import pandas as pd

from kf_lib_data_ingest.app import settings as ingest_settings
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.load.load import LoadStage

from creator.ingest_runs.data_generator.ingest_package.extract_configs.s3_scrape_config import genomic_file_ext  # noqa

GEN_FILE = "genomic_file"
GEN_FILES = "genomic-files"
SEQ_EXP = "sequencing_experiment"
SEQ_EXPS = "sequencing-experiments"
SEQ_EXP_GEN_FILE = "sequencing_experiment_genomic_file"
SEQ_EXP_GEN_FILES = "sequencing-experiment-genomic-files"
BIO_GEN_FILE = "biospecimen_genomic_file"
BIO_GEN_FILES = "biospecimen-genomic-files"
LOAD_ENTITY_TYPES = [GEN_FILE, BIO_GEN_FILE, SEQ_EXP_GEN_FILE]

LOCALHOST = "http://localhost:5000"  # testing
DATASERVICE_URL = LOCALHOST  # During testing


class GenomicDataLoader(object):

    def __init__(self, study_id, init_logger=False):
        self.study_id = study_id

        if init_logger:
            format_ = (
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            root = logging.getLogger()
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(logging.Formatter(format_))
            root.setLevel("INFO")
            root.addHandler(consoleHandler)

        self.logger = logging.getLogger(type(self).__name__)

        self.loader = None
        self.target_api_cfg = ingest_settings.load().TARGET_API_CONFIG

    def ingest_gwo(self, manifest_df):
        """
        Perform the full ingest process for the genomic workflow output files
        (also referred to as "harmonized" files) in _manifest_df_.
        Return the DataFrame used for loading, which is useful for testing.

        1. Load harmonized genomic file metadata (size, filepath, etc)
        2. Link the harmonized files to their related specimens
        3. Link the harmonized files to their related sequencing experiments

        The last two steps need to be done using the harmonized files'
        source genomic files already registered in Data Service since the
        source files have direct relations to the specimens and sequencing
        experiments.
        """
        self.logger.info(
            "Begin the ingest process for genomic workflow output files"
        )
        # -- Step 1: Load harmonized genomic files --
        genomic_df = self.load_harmonized_genomic_files(manifest_df)

        # -- Step 2: Link harmonized genomic files to specimens --
        self.load_specimen_harmonized_gf_links(genomic_df)

        # -- Step 3: Link harmonized genomic files to sequencing experiments --
        genomic_df = self.load_seq_exp_harmonized_genomic_files(genomic_df)

        # Check to make sure everything loaded correctly
        self._validate_load(genomic_df)

        return genomic_df

    def load_harmonized_genomic_files(self, manifest_df):
        """
        Load harmonized genomic file metadata from the manifest into the
        DataService.Scrape S3 to obtain file metadata needed.

        After loading, grab the generated kf_ids from the ingest lib cache,
        join them to _genomic_df_ and then return _genomic_df_. This DataFrame
        is used in the rest of the ingest process
        """
        assert not manifest_df.empty, "Empty manifest DataFrame"

        # Get S3 file metadata
        buckets = set(
            os.path.split(row)[0] for row in manifest_df["Filepath"]
        )
        self.logger.info(f"Getting file metadata from S3 {buckets} ...")

        file_df = utils.scrape_s3(buckets)
        file_df = file_df[~file_df["Filename"].isnull()]

        genomic_df = manifest_df.merge(
            right=file_df, on="Filepath", how="inner"
        )

        # Prepare genomic file df for ingest
        genomic_df = self._prep_harmonized_gf_df(genomic_df)

        df = genomic_df.drop_duplicates([CONCEPT.GENOMIC_FILE.ID])
        self.logger.info(
            f"Loading {df.shape[0]} harmonized genomic files into "
            f"{DATASERVICE_URL}"
        )

        # Load harmonized genomic files
        genomic_cache = self._load_entities(GEN_FILE, df)
        genomic_df = self._get_genomic_file_kf_ids(genomic_cache, genomic_df)

        return genomic_df

    def load_specimen_harmonized_gf_links(self, genomic_df):
        """
        Step 2

        Link the harmonized genomic files to their related specimens by loading
        the appropriate biospecimen-genomic-file records into the Data Service
        """
        # Prepare data
        biospec_gen_df = genomic_df[[
            CONCEPT.GENOMIC_FILE.ID,
            CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID,
            CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID,
        ]]
        biospec_gen_df[CONCEPT.BIOSPECIMEN.ID] = biospec_gen_df[
            CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID
        ]
        biospec_gen_df[CONCEPT.BIOSPECIMEN_GENOMIC_FILE.VISIBLE] = True
        df = biospec_gen_df.drop_duplicates(
            [CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID,
             CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID],
        )

        # Load into Data Service
        self.logger.info(
            f"Creating {df.shape[0]} biospecimen-genomic-file links in "
            f"{DATASERVICE_URL}"
        )
        _ = self._load_entities(BIO_GEN_FILE, df)

        return biospec_gen_df

    def load_seq_exp_harmonized_genomic_files(self, genomic_df):
        """
        Step 3

        Link the harmonized genomic files to their related sequencing
        experiments by loading the appropriate
        sequencing-experiment-genomic-file records into the Data Service

        This will have to be done by getting the sequencing experiments that
        are linked to the source genomic files used to produce the harmonized
        genomic files.
        """
        # Get sequencing experiments for the unharmonized genomic files in
        # the study
        se_source_gf_df = self._get_seq_experiment_genomic_files(
            harmonized=False
        )
        # Merge ^ with the genomic df which as both harmonized and unharmonized
        # gfs in one table
        se_gf_df = pd.merge(
            genomic_df, se_source_gf_df, on=CONCEPT.GENOMIC_FILE.SOURCE_FILE
        )
        se_gf_df[CONCEPT.SEQUENCING_GENOMIC_FILE.VISIBLE] = True

        # Load the harmonized genomic-file sequencing-experiment links
        df = se_gf_df.drop_duplicates(
            [CONCEPT.SEQUENCING.TARGET_SERVICE_ID,
             CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID],
        )
        self.logger.info(
            f"Creating {df.shape[0]} sequencing-experiment-genomic-file "
            f"links in {DATASERVICE_URL}"
        )
        _ = self._load_entities(SEQ_EXP_GEN_FILE, df)

        return se_gf_df

    def _prep_harmonized_gf_df(self, df):
        """
        Part of Step 1

        Clean up the genomic file DataFrame (output from get_s3_file_metadata)
        and get it ready to be ingested by transforming column values and
        standardizing the column names.
        """
        self.logger.info("Preparing genomic file DataFrame for ingest ...")

        df['Hashes'] = df.apply(lambda row: {"ETag": row['ETag']}, axis=1)
        df['urls'] = df.apply(lambda row: [row['Filepath']], axis=1)
        df['file_type'] = df.apply(
            lambda row: genomic_file_ext(row["Filename"]), axis=1,
        )
        col_rename = {
            'KF Biospecimen ID': CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID,
            'Data Type': CONCEPT.GENOMIC_FILE.DATA_TYPE,
            'Filename': CONCEPT.GENOMIC_FILE.FILE_NAME,
            'Hashes': CONCEPT.GENOMIC_FILE.HASH_DICT,
            'Size': CONCEPT.GENOMIC_FILE.SIZE,
            'urls': CONCEPT.GENOMIC_FILE.URL_LIST,
            'file_type': CONCEPT.GENOMIC_FILE.FILE_FORMAT,
            'Filepath': CONCEPT.GENOMIC_FILE.ID,
            'Source Read': CONCEPT.GENOMIC_FILE.SOURCE_FILE,
        }
        df = df[list(col_rename.keys())]
        df.rename(columns=col_rename, inplace=True)
        df[CONCEPT.GENOMIC_FILE.HARMONIZED] = True
        df[CONCEPT.GENOMIC_FILE.VISIBLE] = True

        return df

    def _get_genomic_file_kf_ids(self, ingest_cache, genomic_df):
        """
        Part of Step 1

        Extract the genomic_file KF IDs from the ingest cache and add the IDs
        as a new column to the genomic file DataFrame _genomic_df_.
        Return _genomic_df_
        """
        self.logger.info(
            "Fetching harmonized genomic file KF IDs from ingest cache ..."
        )
        cache_dict = {
            ast.literal_eval(key)['external_id']: value
            for key, value in ingest_cache["genomic_file"].items()
        }
        hash_df = pd.DataFrame(
            list(cache_dict.items()),
            columns=[
                CONCEPT.GENOMIC_FILE.ID, CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID
            ],
        )
        genomic_df = genomic_df.merge(
            right=hash_df,
            on=CONCEPT.GENOMIC_FILE.ID,
            how='inner',
        )
        return genomic_df

    def _get_seq_experiment_genomic_files(self, harmonized=False):
        """
        Part of Step 3

        Get related sequencing experiments for a study's
        genomic files. Returns the DataFrame from step 4.

        1. Get the study's genomic files
        2. Get the study's sequencing-experiments
        3. Get the study's sequencing-experiment-genomic-file links
        4. Extract the KF IDs from step 1, 2, 3
        5. Join DataFrames from 1, 2, 3
        """
        self.logger.info(
            "Fetching sequencing experiment info for source genomic files ..."
        )

        def get_kf_id(link):
            """
            The links given by the DataService yield strings of the form
            /entity-type/kf_id. This function will return the kf_id.
            """
            return link.split('/')[-1]

        dfs = {}
        endpoints = {
            GEN_FILES,
            SEQ_EXP_GEN_FILES,
            SEQ_EXPS,
        }

        # Steps 1-3
        filter_dict = {}
        for endpoint in endpoints:
            if endpoint == GEN_FILES:
                filter_dict = {"harmonized": harmonized}
            dfs[endpoint] = utils.get_entities(
                DATASERVICE_URL, endpoint,
                self.study_id, filter_dict=filter_dict
            )

        # Step 4
        # Source genomic files
        gdf = dfs[GEN_FILES][["kf_id", "external_id"]].rename(
            columns={
                "kf_id": "gf_kf_id",
                "external_id": CONCEPT.GENOMIC_FILE.SOURCE_FILE
            }
        )
        # Sequencing experiments
        sedf = dfs[SEQ_EXPS][
            ["kf_id", "external_id", "_links.sequencing_center"]
        ].rename(
            columns={
                "kf_id": CONCEPT.SEQUENCING.TARGET_SERVICE_ID,
                "external_id": CONCEPT.SEQUENCING.ID,
            }
        )
        SCTID = CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID
        sedf[SCTID] = sedf["_links.sequencing_center"].apply(
            lambda link: get_kf_id(link)
        )

        # Sequencing experiment (source) genomic files
        sgdf = dfs[SEQ_EXP_GEN_FILES][
            [
                "_links.sequencing_experiment",
                "_links.genomic_file",
            ]
        ]
        sgdf["gf_kf_id"] = sgdf["_links.genomic_file"].apply(
            lambda link: get_kf_id(link)
        )
        sgdf[CONCEPT.SEQUENCING.TARGET_SERVICE_ID] = sgdf[
            "_links.sequencing_experiment"].apply(
            lambda link: get_kf_id(link)
        )
        # Merge se-gf with se
        sgdf = pd.merge(sedf, sgdf, on=CONCEPT.SEQUENCING.TARGET_SERVICE_ID)

        # Step 5
        return pd.merge(gdf, sgdf, on="gf_kf_id")[
            [
                CONCEPT.SEQUENCING.TARGET_SERVICE_ID,
                CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID,
                CONCEPT.SEQUENCING.ID,
                CONCEPT.GENOMIC_FILE.SOURCE_FILE,
            ]
        ]

    def _load_entities(self, entity_type, df):
        """
        Uses the ingest lib's load stage to load the entities of _entity_type_
        from DataFrame _df_ into the Data Service
        """
        self.loader = LoadStage(
            self.target_api_cfg,
            DATASERVICE_URL,
            [entity_type],
            self.study_id,
            cache_dir=os.getcwd(),
        )
        self.loader.run({entity_type: df})
        return self.loader.uid_cache

    def _validate_load(self, df):
        # TODO
        pass
