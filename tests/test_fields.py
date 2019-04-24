import pytest
from django.db import models
from creator.fields import KFIDField
from creator.studies.models import Study
from creator.files.models import File


def test_kf_id_prefix_value(db):
    s = Study()
    s.save()
    f = File(study=s)
    f.save()
    assert f.kf_id.startswith("SF")
    assert len(f.kf_id) == 11

    kf_id = f.kf_id
    assert File.objects.get(kf_id=kf_id) == f
