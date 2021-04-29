import pytest
from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.studies.models import Study, SEQ_STATUS_CHOICES
from creator.users.factories import UserFactory


UPDATE_STUDY_SEQUENCING_STATUS_MUTATION = """
mutation updateSeqStatusIP($id: ID!) {
    updateSequencingStatus(study: $id, data: {status: INPROG}) {
        study {
            kfId
            sequencingStatus
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
    Only admins should be allowed to update sequencing status
    """
    user = UserFactory()
    client = clients.get(user_group)
    variables = {"id": to_global_id("StudyNode", mock_study.kf_id)}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={
            "query": UPDATE_STUDY_SEQUENCING_STATUS_MUTATION,
            "variables": variables,
        },
    )

    if allowed:
        resp_body = resp.json()["data"]["updateSequencingStatus"]["study"]
        assert resp_body["sequencingStatus"] == "INPROG"
        assert Study.objects.first().sequencing_status == "INPROG"
    else:
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert Study.objects.first().sequencing_status == "UNKNOWN"
