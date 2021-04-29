import pytest
from django.db import models
from django.contrib.auth import get_user_model
from creator.fields import KFIDField, kf_id_generator
from creator.studies.factories import StudyFactory
from creator.files.models import File

User = get_user_model()


def test_kf_id_prefix_value(db):
    s = StudyFactory()
    user = User(username="user")
    user.save()
    f = File(study=s, creator=user)
    f.save()
    assert f.kf_id.startswith("SF")
    assert len(f.kf_id) == 11

    kf_id = f.kf_id
    assert File.objects.get(kf_id=kf_id) == f


def test_wrong_len():
    """ Test that kf_ids must use a two character prefix """
    with pytest.raises(ValueError) as err:
        kf_id = kf_id_generator("ABC")

        assert "of length 2" in err


def test_user_display_name(db):
    user = User(username="user", first_name="Test", last_name=None)
    assert user.display_name == "Test"

    user = User(username="user", first_name="Test", last_name="User")
    assert user.display_name == "Test User"

    user = User(username="user")
    assert user.display_name == "user"
