import os

from django.conf import settings
from kf_lib_data_ingest.etl.extract.utils import Extractor

from .fixtures import make_template_df
from creator.analyses.file_types import FILE_TYPES


def test_extract_configs():
    """
    Test extract configs in creator/extract_configs/templates by executing
    them with the KF ingest extraction utility and ensure there are no
    exceptions
    """
    extract_config_dir = os.path.join(
        settings.BASE_DIR, "extract_configs", "templates"
    )
    for ft, obj in FILE_TYPES.items():
        ec_file = obj["template"]
        if not ec_file:
            continue
        ec_path = os.path.join(extract_config_dir, ec_file)
        print(f"Testing extract config: {ec_path}")
        assert os.path.exists(ec_path)
        df = make_template_df(ft)
        Extractor().extract(df, ec_path)


def test_optional_cols():
    """
    Test extract configs on data that does not include the optional columns
    specified in the extract configs
    """
    extract_config_dir = os.path.join(
        settings.BASE_DIR, "extract_configs", "templates"
    )
    for ft, obj in FILE_TYPES.items():
        ec_file = obj["template"]
        required_cols = obj["required_columns"]
        if not ec_file:
            continue

        ec_path = os.path.join(extract_config_dir, ec_file)
        print(f"Testing extract config: {ec_path}")
        assert os.path.exists(ec_path)

        # Drop columns that are not required
        df = make_template_df(ft)[required_cols]

        Extractor().extract(df, ec_path)
