import pytest
from hypothesis import given, settings
from hypothesis.strategies import text, integers, characters, dates
from graphql_relay import to_global_id

from creator.files.models import Study
from creator.users.factories import UserFactory


UPDATE_STUDY_MUTATION = """
mutation editStudy($id: ID!, $input: StudyInput!) {
    updateStudy(id: $id, input: $input) {
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
            releaseDate
        }
    }
}
"""


@pytest.fixture
def mock_patch(mocker):
    """ Creates a mock response for the dataservice """
    patch = mocker.patch("requests.patch")

    class MockResp:
        def __init__(self):
            self.status_code = 200

        def json(self):
            return {
                "_links": {
                    "collection": "/studies",
                    "investigator": None,
                    "participants": "/participants?study_id=SD_XQKAP5VX",
                    "self": "/studies/SD_XQKAP5VX",
                    "study_files": "/study-files?study_id=SD_XQKAP5VX",
                },
                "_status": {
                    "code": 200,
                    "message": "study SD_XQKAP5VX updated",
                },
                "results": {
                    "attribution": None,
                    "created_at": "2019-08-05T20:05:26.799916+00:00",
                    "data_access_authority": "dbGaP",
                    "external_id": "NEW",
                    "kf_id": "SD_XQKAP5VX",
                    "modified_at": "2019-08-05T20:07:28.971098+00:00",
                    "name": "testing",
                    "release_status": None,
                    "short_name": None,
                    "version": None,
                    "visible": True,
                },
            }

    patch.return_value = MockResp()
    return patch


@pytest.fixture
def mock_error(mocker):
    """ Mock a failed response from the dataservice """
    patch = mocker.patch("requests.patch")

    class MockResp:
        def __init__(self):
            self.status_code = 400

        def json(self):
            return {"message": "error"}

    patch.return_value = MockResp()
    return patch


@pytest.fixture
def mock_study():
    study = Study(kf_id="SD_XQKAP5VX", external_id="Test Study")
    study.save()
    return study


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
def test_update_study_mutation(
    db,
    admin_client,
    service_client,
    user_client,
    client,
    mock_patch,
    mock_study,
    user_type,
    authorized,
    expected,
):
    """
    Only admins should be allowed to update studies
    """
    user = UserFactory()
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    variables = {
        "id": to_global_id("StudyNode", mock_study.kf_id),
        "input": {
            "externalId": "NEW",
        },
    }
    resp = api_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_STUDY_MUTATION, "variables": variables},
    )

    if expected:
        resp_body = resp.json()["data"]["updateStudy"]["study"]
        assert resp_body["externalId"] == "NEW"
        assert Study.objects.first().external_id == "NEW"
    else:
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")
        assert Study.objects.first().external_id == "Test Study"


def test_dataservice_call(db, admin_client, mock_patch, settings, mock_study):
    """
    Test that the dataservice is called correctly
    """
    variables = {
        "id": to_global_id("StudyNode", mock_study.kf_id),
        "input": {"externalId": "NEW"},
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_STUDY_MUTATION, "variables": variables},
    )

    assert mock_patch.call_count == 1
    mock_patch.assert_called_with(
        f"{settings.DATASERVICE_URL}/studies/{mock_study.kf_id}",
        json={"external_id": "NEW"},
        headers=settings.REQUESTS_HEADERS,
        timeout=settings.REQUESTS_TIMEOUT,
    )
    assert Study.objects.count() == 1


def test_dataservice_feat_flag(
    db, admin_client, mock_patch, settings, mock_study
):
    """
    Test that updating studies does not work when the feature flag is turned
    off.
    """
    settings.FEAT_DATASERVICE_UPDATE_STUDIES = False

    variables = {
        "id": to_global_id("StudyNode", mock_study.kf_id),
        "input": {"externalId": "NEW"},
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_STUDY_MUTATION, "variables": variables},
    )

    assert mock_patch.call_count == 0
    assert Study.objects.first().external_id == "Test Study"
    resp_message = resp.json()["errors"][0]["message"]
    assert resp_message.startswith("Updating studies is not enabled")


def test_dataservice_error(db, admin_client, mock_error, mock_study):
    """
    Test behavior when dataservice returns an error.
    """
    variables = {
        "id": to_global_id("StudyNode", mock_study.kf_id),
        "input": {"externalId": "NEW"},
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_STUDY_MUTATION, "variables": variables},
    )

    assert mock_error.call_count == 1
    assert Study.objects.first().external_id == "Test Study"
    resp_message = resp.json()["errors"][0]["message"]
    assert resp_message.startswith("Problem updating study:")


@given(s=text(alphabet=characters(blacklist_categories=("Cc", "Cs"))))
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
    ],
)
def test_text_fields(
    db, admin_client, settings, mock_patch, mock_study, s, field
):
    """
    Test that text fields may be updated
    """
    variables = {
        "id": to_global_id("StudyNode", mock_study.kf_id),
        "input": {},
    }
    variables["input"][field] = s
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_STUDY_MUTATION, "variables": variables},
    )

    assert "errors" not in resp.json()


@given(s=integers(min_value=0, max_value=2147483647))
@settings(max_examples=10)
@pytest.mark.parametrize("field", ["anticipatedSamples"])
def test_integer_fields(
    db, admin_client, settings, mock_patch, mock_study, s, field
):
    """
    Test that integer fields may be updated
    """
    variables = {
        "id": to_global_id("StudyNode", mock_study.kf_id),
        "input": {},
    }
    variables["input"][field] = s
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_STUDY_MUTATION, "variables": variables},
    )

    assert "errors" not in resp.json()


@given(s=text(alphabet=characters(blacklist_categories=("Cc", "Cs"))))
@settings(max_examples=10)
@pytest.mark.parametrize("field", ["description", "awardeeOrganization"])
def test_internal_fields(db, admin_client, mock_patch, mock_study, s, field):
    """
    Test that inputs for our internal study fields are updated  correctly.
    """
    variables = {
        "id": to_global_id("StudyNode", mock_study.kf_id),
        "input": {},
    }
    variables["input"][field] = s
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_STUDY_MUTATION, "variables": variables},
    )
    assert "errors" not in resp.json()
    assert resp.json()["data"]["updateStudy"]["study"][field] == s


@given(s=dates())
@settings(max_examples=10)
@pytest.mark.parametrize("field", ["releaseDate"])
def test_internal_datetime_fields(
    db, admin_client, mock_patch, mock_study, s, field
):
    """
    Test that inputs for study datetime fields are updated correctly.
    """
    variables = {
        "id": to_global_id("StudyNode", mock_study.kf_id),
        "input": {},
    }
    variables["input"][field] = s
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_STUDY_MUTATION, "variables": variables},
    )
    assert "errors" not in resp.json()
    assert resp.json()["data"]["updateStudy"]["study"][field] == str(s)


def test_update_study_collaborators_not_mutable(
    db, settings, mock_study, mock_patch, admin_client
):
    """
    Collaborators should not be modifiable
    """
    user = UserFactory()
    variables = {
        "id": to_global_id("StudyNode", mock_study.kf_id),
        "input": {
            "externalId": "NEW",
            "collaborators": [to_global_id("UserNode", user.sub)],
        },
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_STUDY_MUTATION, "variables": variables},
    )

    assert Study.objects.first().collaborators.count() == 0
