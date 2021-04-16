import os

from django.conf import settings
from kf_lib_data_ingest.etl.extract.utils import Extractor

from .fixtures import make_template_df, MockVersion
from creator.analyses.file_types import FILE_TYPES
from creator.files.models import extract_config_path


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


def test_extract_config_path(mocker):
    """
    Test the method that finds the best extract config path for a file version
    """
    # Test a version with a valid extract config
    version = MockVersion(file_type="PDA")
    ec = extract_config_path(version)
    assert os.path.exists(ec)
    assert "participant_config.py" == os.path.split(ec)[-1]

    # Test a version with no extract config
    version = MockVersion(file_type="OTH")
    ec = extract_config_path(version)
    assert ec is None

    # Test a version without a root file
    mock_version = mocker.patch("creator.files.models.Version")
    mock_version.root_file.side_effect = Exception
    ec = extract_config_path(mock_version)
    assert ec is None
