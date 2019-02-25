import os
import shutil
import pytest
from django.conf import settings


@pytest.yield_fixture
def tmp_uploads(tmpdir):
    settings.UPLOAD_DIR = os.path.join('./test_uploads', tmpdir)
    yield tmpdir
    shutil.rmtree(str(tmpdir))
