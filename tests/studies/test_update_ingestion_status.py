import pytest
from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.studies.models import Study, ING_STATUS_CHOICES
from creator.users.factories import UserFactory


UPDATE_STUDY_INGESTION_STATUS_MUTATION = """
mutation updateIngStatusIP($id: ID!) {
    updateIngestionStatus(study: $id, data: {status: INPROG}) {
        study {
            kfId
            ingestionStatus
        }
    }
}
"""


@pytest.fixture
def mock_study():
    study = StudyFactory(kf_id="SD_XQKAP5VX", external_id="Test Study")
    study.save()
    return study


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", False),
        ("Investigators", False),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_update_study_mutation(db, clients, mock_study, user_group, allowed):
    """
    Only admins should be allowed to update ingestion status
    """
    user = UserFactory()
    client = clients.get(user_group)
    variables = {"id": to_global_id("StudyNode", mock_study.kf_id)}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={
            "query": UPDATE_STUDY_INGESTION_STATUS_MUTATION,
            "variables": variables,
        },
    )

    if allowed:
        resp_body = resp.json()["data"]["updateIngestionStatus"]["study"]
        assert resp_body["ingestionStatus"] == "INPROG"
        assert Study.objects.first().ingestion_status == "INPROG"
    else:
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert Study.objects.first().ingestion_status == "UNKNOWN"
