import pytest
from hypothesis import given, settings
from hypothesis.strategies import text, integers

from creator.files.models import Study


CREATE_STUDY_MUTATION = """
mutation newStudy($input: StudyInput!) {
    createStudy(input: $input) {
        study {
            kfId
            externalId
            name
            description
            visible
            attribution
            dataAccessAuthority
            releaseStatus
            shortName
            version
            anticipatedSamples
            awardeeOrganization
        }
    }
}
"""


@pytest.fixture
def mock_cavatica(mocker, settings):
    """ Mocks out project setup functions """
    settings.CAVATICA_HARMONIZATION_TOKEN = "testtoken"
    settings.CAVATICA_DELIVERY_TOKEN = "testtoken"
    cavatica = mocker.patch("creator.studies.schema.setup_cavatica")
    return cavatica


@pytest.fixture
def mock_post(mocker):
    """ Creates a mock response for the dataservice """
    post = mocker.patch("requests.post")

    class MockResp:
        def __init__(self):
            self.status_code = 201

        def json(self):
            return {
                "_links": {
                    "collection": "/studies",
                    "investigator": None,
                    "participants": "/participants?study_id=SD_6HET65MK",
                    "self": "/studies/SD_6HET65MK",
                    "study_files": "/study-files?study_id=SD_6HET65MK",
                },
                "_status": {
                    "code": 201,
                    "message": "study SD_6HET65MK created",
                },
                "results": {
                    "attribution": None,
                    "created_at": "2019-08-05T17:50:21.681779+00:00",
                    "data_access_authority": "dbGaP",
                    "external_id": "Test Study",
                    "kf_id": "SD_6HET65MK",
                    "modified_at": "2019-08-05T17:50:21.681802+00:00",
                    "name": "testing",
                    "release_status": None,
                    "short_name": None,
                    "version": None,
                    "visible": True,
                },
            }

    post.return_value = MockResp()
    return post


@pytest.fixture
def mock_error(mocker):
    """ Mock a failed response from the dataservice """
    post = mocker.patch("requests.post")

    class MockResp:
        def __init__(self):
            self.status_code = 400

        def json(self):
            return {"message": "error"}

    post.return_value = MockResp()
    return post


@pytest.mark.parametrize(
    "user_type,authorized,expected",
    [
        ("admin", True, True),
        ("admin", False, True),
        ("service", True, True),
        ("service", False, True),
        ("user", True, False),
        ("user", False, False),
        (None, True, False),
        (None, False, False),
    ],
)
def test_create_study_mutation(
    db,
    admin_client,
    service_client,
    user_client,
    client,
    mock_post,
    mock_cavatica,
    user_type,
    authorized,
    expected,
):
    """
    Only admins should be allowed to create studies
    """
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    variables = {"input": {"externalId": "Test Study"}}
    resp = api_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    if expected:
        resp_body = resp.json()["data"]["createStudy"]["study"]
        assert resp_body["externalId"] == "Test Study"
        assert Study.objects.count() == 1
        assert Study.objects.first().external_id == "Test Study"
        assert mock_cavatica.call_count == 1
    else:
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")
        assert Study.objects.count() == 0
        assert mock_cavatica.call_count == 0


def test_dataservice_call(db, admin_client, mock_post, settings):
    """
    Test that the dataservice is called correctly
    """
    variables = {"input": {"externalId": "Test Study"}}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert mock_post.call_count == 1
    mock_post.assert_called_with(
        f"{settings.DATASERVICE_URL}/studies",
        json={"external_id": "Test Study"},
        headers=settings.REQUESTS_HEADERS,
        timeout=settings.REQUESTS_TIMEOUT,
    )
    assert Study.objects.count() == 1


def test_dataservice_feat_flag(db, admin_client, mock_post, settings):
    """
    Test that creating studies does not work when the feature flag is turned
    off.
    """
    settings.FEAT_DATASERVICE_CREATE_STUDIES = False

    variables = {"input": {"externalId": "Test Study"}}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert mock_post.call_count == 0
    assert Study.objects.count() == 0
    resp_message = resp.json()["errors"][0]["message"]
    assert resp_message.startswith("Creating studies is not enabled")


def test_dataservice_error(db, admin_client, mock_error):
    """
    Test behavior when dataservice returns an error.
    """
    variables = {"input": {"externalId": "Test Study"}}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert mock_error.call_count == 1
    assert Study.objects.count() == 0
    resp_message = resp.json()["errors"][0]["message"]
    assert resp_message.startswith("Problem creating study:")


@given(s=text())
@settings(max_examples=10)
@pytest.mark.parametrize(
    "field",
    [
        "name",
        "visible",
        "attribution",
        "dataAccessAuthority",
        "releaseStatus",
        "shortName",
        "version",
        "description",
        "awardeeOrganization",
    ],
)
def test_text_fields(db, admin_client, settings, mock_post, s, field):
    """
    Test text inputs for different fields
    """
    settings.FEAT_CAVATICA_CREATE_PROJECTS = False

    variables = {"input": {"externalId": "TEST"}}
    variables["input"][field] = s
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert "errors" not in resp.json()


@given(s=integers(min_value=0, max_value=2147483647))
@settings(max_examples=10)
@pytest.mark.parametrize("field", ["anticipatedSamples"])
def test_integer_fields(db, admin_client, settings, mock_post, s, field):
    """
    Test positive integer inputs for different fields
    """
    settings.FEAT_CAVATICA_CREATE_PROJECTS = False

    variables = {"input": {"externalId": "TEST"}}
    variables["input"][field] = s
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert "errors" not in resp.json()
