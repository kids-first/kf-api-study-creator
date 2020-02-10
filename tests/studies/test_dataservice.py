import pytest
from requests.exceptions import RequestException
from django.contrib.auth import get_user_model

from creator.models import Job
from creator.studies.models import Study
from creator.studies.dataservice import sync_dataservice_studies

MOCK_RESP = {
    "_links": {"next": "/studies?after=1529089066.003078", "self": "/studies"},
    "_status": {"code": 200, "message": "success"},
    "limit": 10,
    "results": [
        {
            "_links": {
                "collection": "/studies",
                "investigator": "/investigators/IG_JBKNYBM3",
                "participants": "/participants?study_id=SD_9PYZAHHE",
                "self": "/studies/SD_9PYZAHHE",
                "study_files": "/study-files?study_id=SD_9PYZAHHE",
            },
            "attribution": "https://www.ncbi.nlm.nih.gov/",
            "created_at": "2018-05-22T21:12:42.999818+00:00",
            "data_access_authority": "dbGaP",
            "external_id": "phs001168",
            "kf_id": "SD_9PYZAHHE",
            "modified_at": "2019-08-07T14:30:22.131584+00:00",
            "name": None,
            "release_status": "Pending",
            "short_name": "Kids First: Orofacial Cleft - European Ancestry",
            "version": "v2.p2",
            "visible": True,
        },
        {
            "_links": {
                "collection": "/studies",
                "investigator": "/investigators/IG_4RTENGEW",
                "participants": "/participants?study_id=SD_DYPMEHHF",
                "self": "/studies/SD_DYPMEHHF",
                "study_files": "/study-files?study_id=SD_DYPMEHHF",
            },
            "attribution": "https://www.ncbi.nlm.nih.gov/",
            "created_at": "2018-06-11T13:26:50.673622+00:00",
            "data_access_authority": "dbGaP",
            "external_id": "phs001436",
            "kf_id": "SD_DYPMEHHF",
            "modified_at": "2019-10-01T15:23:31.308197+00:00",
            "name": "Discovering the Genetic Basis of Human Neuroblastoma",
            "release_status": "Pending",
            "short_name": "Kids First: Neuroblastoma",
            "version": "v1.p1",
            "visible": True,
        },
    ],
}


def test_sync_dataservice_studies(db, mocker):
    """
    Test that studies are created from the Dataservice correctly
    """
    req_mock = mocker.patch("creator.studies.dataservice.requests")
    req_mock.get().json.return_value = MOCK_RESP

    assert Study.objects.count() == 0

    sync_dataservice_studies()
    assert Study.objects.count() == 2

    sync_dataservice_studies()
    assert Study.objects.count() == 2


def test_sync_dataservice_studies_deleted(db, mocker):
    """
    Test that studies that have been deleted in the Dataservice are marked
    in the Study Creator
    """
    req_mock = mocker.patch("creator.studies.dataservice.requests")
    req_mock.get().json.return_value = MOCK_RESP

    sync_dataservice_studies()
    assert Study.objects.count() == 2

    DEL_RESP = MOCK_RESP.copy()
    DEL_RESP["results"] = DEL_RESP["results"][:1]
    req_mock.get().json.return_value = DEL_RESP

    sync_dataservice_studies()
    assert Study.objects.count() == 2
    assert Study.objects.get(kf_id="SD_DYPMEHHF").deleted is True
    assert Study.objects.get(kf_id="SD_9PYZAHHE").deleted is False


def test_sync_dataservice_studies_request_error(db, mocker):
    """
    Test that errors in request are handled
    """
    req_mock = mocker.patch("creator.studies.dataservice.requests")
    req_mock.get.side_effect = RequestException

    with pytest.raises(RequestException):
        sync_dataservice_studies()


def test_sync_dataservice_studies_parse_error(db, mocker):
    """
    Test that errors in parsing request are handled
    """
    req_mock = mocker.patch("creator.studies.dataservice.requests")
    req_mock.get().json.side_effect = Exception("parse error")

    with pytest.raises(Exception) as err:
        sync_dataservice_studies()
        assert err == "parse error"
