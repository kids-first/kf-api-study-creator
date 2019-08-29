from unittest.mock import MagicMock
from graphql_relay import to_global_id
from creator.studies.models import Study
from creator.events.models import Event
from django.contrib.auth import get_user_model

User = get_user_model()

CREATE_STUDY = """
mutation ($input: StudyInput!) {
    createStudy(input: $input) {
        study { id kfId externalId name }
    }
}

"""
UPDATE_STUDY = """
mutation ($id: ID! $input: StudyInput!) {
    updateStudy(id: $id, input: $input) {
        study { id kfId externalId name }
    }
}
"""


def test_new_study_event(admin_client, db, mocker, settings):
    """
    Test that new studies creates an event
    """
    settings.FEAT_CAVATICA_CREATE_PROJECTS = False
    post = mocker.patch("requests.post")
    MockResp = MagicMock()
    MockResp.status_code = 201
    MockResp.json.return_value = {"results": {"kf_id": "ABCABCBA"}}
    post.return_value = MockResp

    variables = {"input": {"externalId": "TEST"}}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY, "variables": variables},
    )

    assert Event.objects.count() == 1
    assert Event.objects.filter(event_type="SD_CRE").count() == 1

    sd_cre = Event.objects.filter(event_type="SD_CRE").first()
    assert sd_cre.user == User.objects.first()
    assert sd_cre.file is None
    assert sd_cre.study == Study.objects.first()


def test_update_study_event(admin_client, db, mocker):
    """
    Test that updating studies creates an event
    """
    patch = mocker.patch("requests.patch")
    MockResp = MagicMock()
    MockResp.status_code = 200
    MockResp.json.return_value = {"results": {"kf_id": "ABCABCBA"}}
    patch.return_value = MockResp

    study = Study(kf_id="SD_ABCABCBA", external_id="TEST")
    study.save()

    variables = {
        "id": to_global_id("StudyNode", study.kf_id),
        "input": {"externalId": "TESTING"},
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_STUDY, "variables": variables},
    )

    assert Event.objects.count() == 1
    assert Event.objects.filter(event_type="SD_UPD").count() == 1

    sd_upd = Event.objects.filter(event_type="SD_UPD").first()
    assert sd_upd.user == User.objects.first()
    assert sd_upd.file is None
    assert sd_upd.study == Study.objects.first()