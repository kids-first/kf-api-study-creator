import pytest

from creator.studies.factories import StudyFactory
from creator.storage_analyses.factories import ExpectedFileFactory
from creator.storage_analyses import utils
from creator.storage_analyses.models import ExpectedFile

from ..files.fixtures import make_file_upload_manifest


def test_chunked_dataframe_reader(db, mocker, make_file_upload_manifest):
    """
    Test utils.chunked_dataframe_reader
    """
    # Success
    version = make_file_upload_manifest(nrows=100)
    for i, df in enumerate(
        utils.chunked_dataframe_reader(version, batch_size=10)
    ):
        assert df.shape[0] == 10
    assert i == 9

    # Unknown file format
    version = make_file_upload_manifest(filename="foo.bar")
    with pytest.raises(IOError):
        next(utils.chunked_dataframe_reader(version))

    # Problem reading data
    mock_logger = mocker.patch("creator.storage_analyses.utils.logger")
    with pytest.raises(Exception):
        next(utils.chunked_dataframe_reader(version, batchsize="foo"))
        assert mock_logger.exception.call_count == 1


def test_batched_queryset_iterator(db):
    """
    Test utils.batched_queryset_iterator
    """
    files = ExpectedFileFactory.create_batch(10)
    for i, batch in (
        enumerate(utils.batched_queryset_iterator(ExpectedFile.objects, 5))
    ):
        assert len(batch) == 5
    assert i == 1


def test_bulk_upsert_expected_files(db):
    """
    Test utils.bulk_upsert_expected_files
    """
    study = StudyFactory()
    files = [
        {
            "study": study,
            "file_location": f"myfile{i}.tsv",
            "hash": f"foobar{i}",
            "hash_algorithm": "MD5",
            "size": i * 100

        } for i in range(5)
    ]
    assert ExpectedFile.objects.count() == 0
    utils.bulk_upsert_expected_files(files)
    assert ExpectedFile.objects.count() == 5
