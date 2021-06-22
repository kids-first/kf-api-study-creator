from unittest.mock import MagicMock
from graphql_relay import to_global_id
from creator.studies.models import Study
from creator.projects.models import Project
from creator.events.models import Event
from creator.studies.factories import StudyFactory
from creator.organizations.factories import OrganizationFactory
from django.contrib.auth import get_user_model

User = get_user_model()

CREATE_STUDY = """
mutation ($input: CreateStudyInput!) {
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


def test_new_study_event(
    permission_client, db, mocker, settings, mock_cavatica_api
):
    """
    Test that new studies creates an event
    """
    user, client = permission_client(["add_study"])
    settings.FEAT_CAVATICA_CREATE_PROJECTS = True
    settings.CAVATICA_HARMONIZATION_TOKEN = "abc"
    settings.CAVATICA_DELIVERY_TOKEN = "abc"
    organization = OrganizationFactory(members=[user])

    post = mocker.patch("requests.post")
    MockResp = MagicMock()
    MockResp.status_code = 201
    MockResp.json.return_value = {"results": {"kf_id": "ABCABCBA"}}
    post.return_value = MockResp

    variables = {
        "input": {
            "externalId": "TEST",
            "organization": to_global_id("OrganizationNode", organization.pk),
        }
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY, "variables": variables},
    )

    assert Event.objects.count() == 4
    assert Event.objects.filter(event_type="SD_CRE").count() == 1

    sd_cre = Event.objects.filter(event_type="SD_CRE").first()
    assert sd_cre.user == user
    assert sd_cre.file is None
    assert sd_cre.study == Study.objects.first()

    assert Event.objects.filter(event_type="PR_STR").count() == 1
    assert Event.objects.filter(event_type="PR_SUC").count() == 1

    assert Event.objects.filter(event_type="PR_CRE").count() == 1
    pr_cre = Event.objects.filter(event_type="PR_CRE").first()
    assert pr_cre.file is None
    assert pr_cre.version is None
    assert pr_cre.study == Study.objects.first()
    assert pr_cre.project in Project.objects.all()


def test_update_study_event(permission_client, db, mocker):
    """
    Test that updating studies creates an event
    """
    user, client = permission_client(["change_study"])
    patch = mocker.patch("requests.patch")
    MockResp = MagicMock()
    MockResp.status_code = 200
    MockResp.json.return_value = {"results": {"kf_id": "ABCABCBA"}}
    patch.return_value = MockResp

    study = StudyFactory(kf_id="SD_ABCABCBA", external_id="TEST")
    study.save()

    variables = {
        "id": to_global_id("StudyNode", study.kf_id),
        "input": {"externalId": "TESTING"},
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_STUDY, "variables": variables},
    )

    assert Event.objects.count() == 1
    assert Event.objects.filter(event_type="SD_UPD").count() == 1

    sd_upd = Event.objects.filter(event_type="SD_UPD").first()
    assert sd_upd.user == user
    assert sd_upd.file is None
    assert sd_upd.study == Study.objects.first()
