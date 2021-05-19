from creator.ingest_runs import utils
from django.conf import settings
import ast
import logging
import os
import pandas as pd
from pprint import pformat

from kf_lib_data_ingest.app import settings as ingest_settings
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.common.pandas_utils import outer_merge
from kf_lib_data_ingest.etl.load.load_v2 import LoadStage

from creator.events.models import Event
from creator.studies.data_generator.ingest_package.extract_configs.s3_scrape_config import genomic_file_ext  # noqa

GWO_MANIFEST = "GWO Manifest"
GEN_FILE = "genomic_file"
GEN_FILES = "genomic-files"
BIOSPECIMEN = "biospecimen"
BIOSPECIMENS = "biospecimens"
SEQ_EXP = "sequencing_experiment"
SEQ_EXPS = "sequencing-experiments"
SEQ_EXP_GEN_FILE = "sequencing_experiment_genomic_file"
SEQ_EXP_GEN_FILES = "sequencing-experiment-genomic-files"
BIO_GEN_FILE = "biospecimen_genomic_file"
BIO_GEN_FILES = "biospecimen-genomic-files"
LOAD_ENTITY_TYPES = {GEN_FILE, BIO_GEN_FILE, SEQ_EXP_GEN_FILE}

logger = logging.getLogger(__name__)


class GenomicDataLoader(object):
    def __init__(self, study, ingest_run):
        self.study = study
        self.study_id = study.kf_id
        self.ingest_run = ingest_run
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
        logger.info(
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
        DataService. Scrape S3 to obtain file metadata needed.

        After loading, grab the generated kf_ids from the ingest lib cache,
        join them to _genomic_df_ and then return _genomic_df_. This DataFrame
        is used in the rest of the ingest process
        """
        assert not manifest_df.empty, "Empty manifest DataFrame"

        # Get S3 file metadata
        buckets = set(os.path.split(row)[0] for row in manifest_df["Filepath"])
        logger.info(f"Getting file metadata from S3 {buckets} ...")

        file_df = utils.scrape_s3(buckets)
        file_df.dropna(subset=["Filename"], inplace=True)

        # Check for any discrepancy between between the files listed in the
        # GWO manifest and the S3 scrape, then merge the two DataFrames
        genomic_df = self._merge_and_validate(
            manifest_df,
            file_df,
            GWO_MANIFEST,
            "S3 bucket",
            on="Filepath",
        )

        # Prepare genomic file df for ingest
        genomic_df = self._prep_harmonized_gf_df(genomic_df)

        df = genomic_df.drop_duplicates([CONCEPT.GENOMIC_FILE.ID])
        logger.info(
            f"Loading {df.shape[0]} harmonized genomic files into "
            f"{settings.DATASERVICE_URL}"
        )

        # Load harmonized genomic files
        genomic_cache = self._load_entities(GEN_FILE, df)
        genomic_df = self._get_genomic_file_kf_ids(genomic_cache, genomic_df)

        return genomic_df

    def _merge_and_validate(
        self,
        left_df,
        right_df,
        left_df_name,
        right_df_name,
        custom_message=None,
        **outer_merge_kwargs,
    ):
        """
        Merge two DataFrames together and report any missing data. Missing
        data is defined as any records that are in the left DataFrame but
        not in the right DataFrame.
        """
        outer_merge_kwargs["with_merge_detail_dfs"] = True
        _, inner_merge_df, left_only, _ = outer_merge(
            left_df,
            right_df,
            **outer_merge_kwargs,
        )
        key = None
        for kwarg in ("on", "left_on", "right_on"):
            key = outer_merge_kwargs.get(kwarg)
            if key:
                break
        missing = left_only[key].drop_duplicates()
        if not missing.empty:
            num_missing = missing.shape[0]
            message = (
                f"During the ingest GWO run: {self.ingest_run.pk}, "
                f"{num_missing} records in the {left_df_name} were not found "
                f"in the {right_df_name}:\n{pformat(missing)}"
            )
            self._create_missing_event(message)
            logger.warning(message)
            if custom_message is not None:
                logger.warning(custom_message)
        return inner_merge_df

    def _create_missing_event(self, message):
        """
        Upon detection of discrepancies that occur during the GWO ingest
        process, fire off an Event.
        """
        first_version = self.ingest_run.versions.first()
        ev = Event(
            study=self.study,
            file=first_version.root_file,
            version=first_version,
            user=self.ingest_run.creator,
            description=message,
            event_type="IR_MIS",
            organization_id=self.study.organization.pk,
        )
        ev.save()

    def load_specimen_harmonized_gf_links(self, genomic_df):
        """
        Step 2

        Link the harmonized genomic files to their related specimens by loading
        the appropriate biospecimen-genomic-file records into the Data Service
        """
        # Prepare data
        biospec_gen_df = genomic_df[
            [
                CONCEPT.GENOMIC_FILE.ID,
                CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID,
                CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID,
            ]
        ].copy()
        biospec_gen_df[CONCEPT.BIOSPECIMEN.ID] = biospec_gen_df[
            CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID
        ]
        biospec_gen_df[CONCEPT.BIOSPECIMEN_GENOMIC_FILE.VISIBLE] = True
        load_df = biospec_gen_df.drop_duplicates(
            [
                CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID,
                CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID,
            ],
        )

        # Detect and report if there is a discrepancy between the specimens
        # listed in the GWO manifest and the specimens in Dataservice
        bio_df = utils.get_entities(
            settings.DATASERVICE_URL,
            BIOSPECIMENS,
            self.study_id,
        )
        self._merge_and_validate(
            load_df,
            bio_df,
            GWO_MANIFEST,
            "DataService",
            left_on=CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID,
            right_on="kf_id",
        )
        # Load into Data Service
        logger.info(
            f"Creating {load_df.shape[0]} biospecimen-genomic-file links in "
            f"{settings.DATASERVICE_URL}"
        )
        _ = self._load_entities(BIO_GEN_FILE, load_df)

        return load_df

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
        se_source_gf_df = self._get_seq_experiment_genomic_files(genomic_df)
        # Merge ^ with the genomic df which has both harmonized and
        # unharmonized gfs in one table
        se_gf_df = pd.merge(
            genomic_df, se_source_gf_df, on=CONCEPT.GENOMIC_FILE.SOURCE_FILE
        )
        se_gf_df.loc[:, CONCEPT.SEQUENCING_GENOMIC_FILE.VISIBLE] = True

        # Load the harmonized genomic-file sequencing-experiment links
        df = se_gf_df.drop_duplicates(
            [
                CONCEPT.GENOMIC_FILE.SOURCE_FILE,
                CONCEPT.SEQUENCING.ID,
            ]
        )
        logger.info(
            f"Creating {df.shape[0]} sequencing-experiment-genomic-file "
            f"links in {settings.DATASERVICE_URL}"
        )
        _ = self._load_entities(SEQ_EXP_GEN_FILE, df)

        return df

    def _prep_harmonized_gf_df(self, df):
        """
        Part of Step 1

        Clean up the genomic file DataFrame (_manifest_df_ joined with S3
        data obtained from utils.scrape_s3) and get it ready to be ingested
        by transforming column values and standardizing the column names.
        """
        logger.info("Preparing genomic file DataFrame for ingest ...")

        df["Hashes"] = df.apply(lambda row: {"ETag": row["ETag"]}, axis=1)
        df["urls"] = df.apply(lambda row: [row["Filepath"]], axis=1)
        df["file_type"] = df.apply(
            lambda row: genomic_file_ext(row["Filename"]),
            axis=1,
        )
        col_rename = {
            "KF Biospecimen ID": CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID,
            "Data Type": CONCEPT.GENOMIC_FILE.DATA_TYPE,
            "Filename": CONCEPT.GENOMIC_FILE.FILE_NAME,
            "Hashes": CONCEPT.GENOMIC_FILE.HASH_DICT,
            "Size": CONCEPT.GENOMIC_FILE.SIZE,
            "urls": CONCEPT.GENOMIC_FILE.URL_LIST,
            "file_type": CONCEPT.GENOMIC_FILE.FILE_FORMAT,
            "Filepath": CONCEPT.GENOMIC_FILE.ID,
            "Source Read": CONCEPT.GENOMIC_FILE.SOURCE_FILE,
        }

        df = df[list(col_rename.keys())].rename(columns=col_rename)
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
        logger.info(
            "Fetching harmonized genomic file KF IDs from ingest cache ..."
        )
        cache_dict = {
            ast.literal_eval(key)["external_id"]: value
            for key, value in ingest_cache["genomic_file"].items()
        }
        hash_df = pd.DataFrame(
            list(cache_dict.items()),
            columns=[
                CONCEPT.GENOMIC_FILE.ID,
                CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID,
            ],
        )
        genomic_df = genomic_df.merge(
            right=hash_df,
            on=CONCEPT.GENOMIC_FILE.ID,
            how="inner",
        )
        return genomic_df

    def _get_seq_experiment_genomic_files(self, genomic_df):
        """
        Part of Step 3

        Get related sequencing experiments for a study's
        genomic files. Returns the DataFrame from step 5.

        1. Get the study's unharmonized genomic files
        2. Get the study's sequencing-experiments
        3. Get the study's sequencing-experiment-genomic-file links
        4. Extract the KF IDs from step 1, 2, 3
        5. Join DataFrames from 1, 2, 3
        """
        logger.info(
            "Fetching sequencing experiment info for source genomic files ..."
        )

        def get_kf_id(link):
            """
            The links given by the DataService yield strings of the form
            /entity-type/kf_id. This function will return the kf_id.
            """
            return link.split("/")[-1]

        dfs = {}
        endpoints = {
            GEN_FILES,
            SEQ_EXP_GEN_FILES,
            SEQ_EXPS,
        }

        # Steps 1-3
        for endpoint in endpoints:
            filter_dict = (
                {"is_harmonized": False} if endpoint == GEN_FILES else None
            )
            dfs[endpoint] = utils.get_entities(
                settings.DATASERVICE_URL,
                endpoint,
                self.study_id,
                filter_dict=filter_dict,
            )

        # Step 4
        # Source genomic files
        gdf = dfs[GEN_FILES][["kf_id", "external_id"]].rename(
            columns={
                "kf_id": "gf_kf_id",
                "external_id": CONCEPT.GENOMIC_FILE.SOURCE_FILE,
            }
        )
        # Check that each unharmonized genomic file
        # in the GWO manifest has a corresponding entity in the DataService
        self._merge_and_validate(
            gdf[[CONCEPT.GENOMIC_FILE.SOURCE_FILE]],
            genomic_df[[CONCEPT.GENOMIC_FILE.SOURCE_FILE]],
            GWO_MANIFEST,
            "DataService",
            on=CONCEPT.GENOMIC_FILE.SOURCE_FILE,
            custom_message=(
                "The above message refers to the genomic file entities "
                "themselves."
            ),
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
            "_links.sequencing_experiment"
        ].apply(lambda link: get_kf_id(link))

        # Check that each of these unharmonized genomic files has a
        # corresponding sequencing-experiment-genomic-file entity, linking it
        # to a sequencing experiment
        ds_gfs_df = pd.merge(
            gdf,
            genomic_df,
            on=CONCEPT.GENOMIC_FILE.SOURCE_FILE,
        )
        GF_KF_ID = "gf_kf_id"
        self._merge_and_validate(
            ds_gfs_df[[GF_KF_ID]],
            sgdf,
            GWO_MANIFEST,
            "DataService",
            on=GF_KF_ID,
            custom_message=(
                "The above message refers to missing "
                "sequencing-experiment-genomic-file entities."
            ),
        )

        # Merge se-gf with se
        sgdf = pd.merge(sedf, sgdf, on=CONCEPT.SEQUENCING.TARGET_SERVICE_ID)

        # Step 5
        return pd.merge(gdf, sgdf, on=GF_KF_ID)[
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
        from DataFrame _df_ into the Data Service.
        """
        self.loader = LoadStage(
            self.target_api_cfg,
            settings.DATASERVICE_URL,
            [entity_type],
            self.study_id,
            cache_dir=os.getcwd(),
        )
        self.loader.logger = logger
        self.loader.logger.setLevel(logging.DEBUG)
        self.loader.run({entity_type: df})
        return self.loader.uid_cache

    def _validate_load(self, df):
        # TODO
        pass
