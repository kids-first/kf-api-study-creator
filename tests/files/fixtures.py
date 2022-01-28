import os
import pytest
import pandas
from django.core.files.base import ContentFile

from creator.files.factories import VersionFactory
from creator.storage_analyses.models import (
    FILE_UPLOAD_MANIFEST_SCHEMA as MANIFEST_SCHEMA,
)


@pytest.fixture
def make_version(tmpdir, settings):
    """Helper to make a file Version with real content"""

    def _make_version(df):
        version = VersionFactory(size=123)
        content = df.to_csv(sep="\t", index=False)
        settings.BASE_DIR = os.path.join(tmpdir, "test")
        version.key.save("test_file.tsv", ContentFile(content))

        return version
    return _make_version


@pytest.fixture
def make_file_upload_manifest(tmpdir, settings):
    """
    Make a file Version with content that conforms to the file upload manifest
    schema
    """
    def _make(nrows=10, filename="upload_manifest.tsv"):
        version = VersionFactory()
        df = pandas.DataFrame(
            [
                {c: c for c in MANIFEST_SCHEMA["required"]}
                for i in range(nrows)
            ]
        )
        content = df.to_csv(sep="\t", index=False)
        settings.BASE_DIR = os.path.join(tmpdir, "test")
        version.key.save(filename, ContentFile(content))

        return version

    return _make
