import pytest
from django.contrib.auth import get_user_model
from creator.studies.factories import StudyFactory
from django.test.client import Client

User = get_user_model()


SUBSCRIBE_TO = """
    mutation ($studyId: String!) {
        subscribeTo(studyId: $studyId) {
            success
            user {
                username
                studySubscriptions {
                    edges { node { kfId } }
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "user_type,expected",
    [("admin", True), ("service", False), ("user", True), (None, False)],
)
def test_subscribe_own(db, token, service_token, user_type, expected):
    """
    Test that a user may or may not subscribe to a study that is in their
    groups.

    admin - can subscribe to any study
    service - can not subscribe to studies
    user - can subscribe to any study they are in the group of
    unauthed - can not subscribe to studies
    """
    studies = StudyFactory.create_batch(25)
    study = studies[0]

    api_token = {
        "admin": f"Bearer {token([], ['ADMIN'])}",
        "service": service_token(),
        "user": f"Bearer {token([study.kf_id], ['USER'])}",
        None: None,
    }[user_type]
    client = Client(HTTP_AUTHORIZATION=api_token)

    resp = client.post(
        "/graphql",
        data={"query": SUBSCRIBE_TO, "variables": {"studyId": study.kf_id}},
        content_type="application/json",
    )

    if expected:
        assert (
            resp.json()["data"]["subscribeTo"]["user"]["studySubscriptions"][
                "edges"
            ][0]["node"]["kfId"]
            == study.kf_id
        )
        if user_type not in [None, "service"]:
            assert User.objects.first().study_subscriptions.count() == 1
            assert (
                User.objects.first().study_subscriptions.first().kf_id
                == study.kf_id
            )
    else:
        assert (
            resp.json()["errors"][0]["message"]
            == "Not authenticated to subscribe"
        )
        if user_type not in [None, "service"]:
            assert User.objects.first().study_subscriptions.count() == 0


@pytest.mark.parametrize(
    "user_type,expected",
    [("admin", True), ("service", False), ("user", False), (None, False)],
)
def test_subscribe_other(db, token, service_token, user_type, expected):
    """
    Test that a user may or may not subscribe to a study that is not in their
    groups.

    admin - can subscribe to any study
    service - can not subscribe to studies
    user - can subscribe to any study they are in the group of
    unauthed - can not subscribe to studies
    """
    studies = StudyFactory.create_batch(25)
    api_token = {
        "admin": f"Bearer {token([], ['ADMIN'])}",
        "service": service_token(),
        "user": f"Bearer {token([], ['USER'])}",
        None: None,
    }[user_type]
    client = Client(HTTP_AUTHORIZATION=api_token)

    resp = client.post(
        "/graphql",
        data={
            "query": SUBSCRIBE_TO,
            "variables": {"studyId": studies[0].kf_id},
        },
        content_type="application/json",
    )

    if expected:
        assert (
            resp.json()["data"]["subscribeTo"]["user"]["studySubscriptions"][
                "edges"
            ][0]["node"]["kfId"]
            == studies[0].kf_id
        )
        if user_type not in [None, "service"]:
            assert User.objects.first().study_subscriptions.count() == 1
            assert (
                User.objects.first().study_subscriptions.first().kf_id
                == studies[0].kf_id
            )
    else:
        assert (
            resp.json()["errors"][0]["message"]
            == "Not authenticated to subscribe"
        )
        if user_type not in [None, "service"]:
            assert User.objects.first().study_subscriptions.count() == 0


def test_subscribe_does_not_exist(db, admin_client):
    """
    Test that a study that does not exist cannot be subscribed to.
    """
    studies = StudyFactory.create_batch(25)

    resp = admin_client.post(
        "/graphql",
        data={"query": SUBSCRIBE_TO, "variables": {"studyId": "SD_XXXXXXXX"}},
        content_type="application/json",
    )

    assert resp.json()["errors"][0]["message"] == "Study does not exist."
