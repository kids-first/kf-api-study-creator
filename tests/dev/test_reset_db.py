import pytest
from creator.studies.models import Study


def test_reset_db_mounted(db, client, settings, reload_urls):
    """
    Test that the dev endpoint is not mounted unless it is enabled
    """
    reload_urls(settings)
    resp = client.post("/__dev/reset-db/")
    assert resp.status_code == 404

    settings.DEVELOPMENT_ENDPOINTS = True
    reload_urls(settings)

    resp = client.post("/__dev/reset-db/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_post_only(db, client, dev_endpoints):
    """
    Test that endpoints only work for post
    """

    resp = client.get("/__dev/reset-db/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "fail"
    assert resp.json()["message"] == "Only POST is supported"


def test_idempotent(transactional_db, client, dev_endpoints):
    """
    Test that endpoints only work for post
    """

    resp = client.post("/__dev/reset-db/")
    assert Study.objects.count() == 4
    studies_1 = [study.kf_id for study in Study.objects.all()]

    resp = client.post("/__dev/reset-db/")
    assert Study.objects.count() == 4
    studies_2 = [study.kf_id for study in Study.objects.all()]
    assert studies_1 == studies_2
