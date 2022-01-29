
from unittest.mock import MagicMock
import pytest
import json
from graphql import GraphQLError
from requests.exceptions import RequestException

from creator.dewrangle.client import DewrangleClient
from creator.studies.factories import StudyFactory
from creator.organizations.factories import OrganizationFactory


@pytest.fixture
def mock_response():
    """Return a func to generate mock requests Response object"""
    def _mock_response(status_code, resp):
        mock = MagicMock()
        mock.json.return_value = resp
        mock.status_code = status_code
        return mock
    return _mock_response


@pytest.fixture
def mock_dewrangle(mocker, mock_response, settings):
    """Return a func to generate mock dewrangle client"""

    def _mock_dewrangle(status_code=None, resp=None):
        mock_requests = mocker.patch("creator.dewrangle.client.requests")
        mock_session = mock_requests.Session()
        mock_resp = mock_response(status_code, resp)
        mock_session = mock_requests.Session()
        mock_session.headers = {}
        mock_session_post = mock_session.post.return_value = mock_resp

        settings.DATA_TRACKER_DEWRANGLE_SECRET = "supersecret"
        settings.DEWRANGLE_URL = "https://dewrangle.org"
        client = DewrangleClient()

        return client

    return _mock_dewrangle


def test_client_setup(mock_dewrangle):
    """
    Test DewrangleClient init
    """
    client = mock_dewrangle()
    assert client.url == "https://dewrangle.org"
    assert client.session.headers["X-Api-Key"] == "supersecret"
    assert client.session.headers["Content-Type"] == (
        "application/json"
    )


def test_send_post_request(mocker, mock_response, settings):
    """
    Test DewrangleClient._send_post_request helper
    """
    settings.DATA_TRACKER_DEWRANGLE_SECRET = "supersecret"
    settings.DEWRANGLE_URL = "https://dewrangle.org"
    mock_requests = mocker.patch("creator.dewrangle.client.requests")

    success_resp = {"success": "results"}
    mock_resp = mock_response(200, success_resp)
    mock_session = mock_requests.Session()
    mock_session_post = mock_session.post.return_value = mock_resp

    # Success
    client = DewrangleClient()
    resp, status_code = client._send_post_request({"foo": "bar"})
    assert resp == success_resp
    assert status_code == 200

    # Failures
    # Badly formatted json
    mock_resp.json.side_effect = json.JSONDecodeError("", "", 0)
    mock_session_post = mock_session.post.return_value = mock_resp
    with pytest.raises(json.JSONDecodeError):
        client._send_post_request({"foo": "bar"})
        mock_logger.exception.call_count == 1

    # Http Error
    mock_resp.reset_mock()
    mock_resp.raise_for_status.side_effect = RequestException
    mock_session_post = mock_session.post.return_value = mock_resp
    with pytest.raises(RequestException):
        client._send_post_request({"foo": "bar"})


def test_send_mutation(mocker, mock_response):
    """
    Test DewrangleClient.send_mutation helper
    """
    mock_requests = mocker.patch("creator.dewrangle.client.requests")

    success_resp = {"data": "results"}
    mock_resp = mock_response(200, success_resp)
    mock_session = mock_requests.Session()
    mock_session_post = mock_session.post.return_value = mock_resp

    # Success
    client = DewrangleClient()
    resp, code = client._send_mutation({"mutation": "body"}, "mutation")
    assert resp == success_resp

    # Failures
    # Errors in resp
    mock_resp.json.return_value = {"errors": "something went wrong"}
    mock_session_post = mock_session.post.return_value = mock_resp
    with pytest.raises(GraphQLError):
        client._send_mutation({"mutation": "body"}, "mutation")

    # Unexpected resp format
    mock_resp.json.return_value = {"foobar": "unexpected resp"}
    mock_session_post = mock_session.post.return_value = mock_resp
    with pytest.raises(GraphQLError):
        client._send_mutation({"mutation": "body"}, "mutation")


def test_get_node(mock_dewrangle):
    """
    Test DewrangleClient.get_node
    """
    success_resp = {"data": {"node": {"mynode": "foo"}}}
    client = mock_dewrangle(200, success_resp)
    resp = client.get_node(success_resp)
    assert resp == {"mynode": "foo"}


def test_create_study(db, mock_dewrangle):
    """
    Test DewrangleClient create study mutation
    """
    study = StudyFactory()
    resp = {
        "data": {
            "studyCreate": {
                "study": {
                    "id": "dewrangle_study_id",
                    "name": study.name,
                }
            }
        }
    }
    client = mock_dewrangle(200, resp)
    assert study.dewrangle_id is None
    results = client.create_study(study)
    assert study.dewrangle_id == results["id"]
    assert study.name == results["name"]


def test_update_study(db, mock_dewrangle):
    """
    Test DewrangleClient update study mutation
    """
    study = StudyFactory(dewrangle_id="dewrangle_study_id")
    resp = {
        "data": {
            "studyUpdate": {
                "study": {
                    "id": study.dewrangle_id,
                    "name": study.name,
                }
            }
        }
    }
    client = mock_dewrangle(200, resp)
    results = client.update_study(study)
    assert study.dewrangle_id == results["id"]
    assert study.name == results["name"]


def test_upsert_study(mocker, db):
    """
    Test DewrangleClient upsert study
    """
    mock_requests = mocker.patch("creator.dewrangle.client.requests")
    mock_create_study = mocker.patch(
        "creator.dewrangle.client.DewrangleClient.create_study"
    )
    mock_update_study = mocker.patch(
        "creator.dewrangle.client.DewrangleClient.update_study"
    )
    mock_get_node = mocker.patch(
        "creator.dewrangle.client.DewrangleClient.get_node"
    )
    study = StudyFactory()
    client = DewrangleClient()

    # Create new study
    mock_get_node.return_value = None
    results = client.upsert_study(study)
    mock_create_study.call_count == 1

    # Update study
    mock_get_node.return_value = {"study": "foobar"}
    results = client.upsert_study(study)
    mock_update_study.call_count == 1


def test_create_organization(db, mock_dewrangle):
    """
    Test DewrangleClient create organization mutation
    """
    organization = OrganizationFactory()
    resp = {
        "data": {
            "organizationCreate": {
                "organization": {
                    "id": "dewrangle_organization_id",
                    "name": organization.name,
                }
            }
        }
    }
    client = mock_dewrangle(200, resp)
    assert organization.dewrangle_id is None
    results = client.create_organization(organization)
    assert organization.dewrangle_id == results["id"]
    assert organization.name == results["name"]


def test_update_organization(db, mock_dewrangle):
    """
    Test DewrangleClient update organization mutation
    """
    organization = OrganizationFactory(
        dewrangle_id="dewrangle_organization_id"
    )
    resp = {
        "data": {
            "organizationUpdate": {
                "organization": {
                    "id": organization.dewrangle_id,
                    "name": organization.name,
                }
            }
        }
    }
    client = mock_dewrangle(200, resp)
    results = client.update_organization(organization)
    assert organization.dewrangle_id == results["id"]
    assert organization.name == results["name"]


def test_upsert_organization(mocker, db):
    """
    Test DewrangleClient upsert organization
    """
    mock_requests = mocker.patch("creator.dewrangle.client.requests")
    mock_create_organization = mocker.patch(
        "creator.dewrangle.client.DewrangleClient.create_organization"
    )
    mock_update_organization = mocker.patch(
        "creator.dewrangle.client.DewrangleClient.update_organization"
    )
    mock_get_node = mocker.patch(
        "creator.dewrangle.client.DewrangleClient.get_node"
    )
    organization = OrganizationFactory()
    client = DewrangleClient()

    # Create new organization
    mock_get_node.return_value = None
    results = client.upsert_organization(organization)
    mock_create_organization.call_count == 1

    # Update organization
    mock_get_node.return_value = {"organization": "foobar"}
    results = client.upsert_organization(organization)
    mock_update_organization.call_count == 1


def test_bulk_upsert_expected_file(db, mock_dewrangle):
    """
    Test DewrangleClient bulk upsert expected files mutation
    """
    study = StudyFactory(dewrangle_id="dewrangle_study_id")
    files = [
        {
            "file_location": f"myfile{i}.tsv",
            "hash": f"foobar{i}",
            "hash_algorithm": "MD5",
            "size": i * 100

        } for i in range(5)
    ]

    resp = {
        "data": {
            "expectedFileUpsertMany": {
                "total": 5,
                "count": 5
            }
        }
    }
    client = mock_dewrangle(200, resp)
    results = client.bulk_upsert_expected_files(study.dewrangle_id, files)
    assert results["total"] == 5
    assert results["count"] == 5
