import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
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

UNSUBSCRIBE_FROM = """
    mutation ($studyId: String!) {
        unsubscribeFrom(studyId: $studyId) {
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
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", False),
        ("Investigators", True),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_subscribe_own(db, clients, user_group, allowed):
    """
    Test that a user may or may not subscribe to a study that is in their
    groups.

    admin - can subscribe to any study
    service - can not subscribe to studies
    user - can subscribe to any study they are in the group of
    unauthed - can not subscribe to studies
    """
    client = clients.get(user_group)

    studies = StudyFactory.create_batch(25)
    study = studies[0]

    group = Group.objects.filter(name=user_group).first()
    if group:
        user = group.user_set.first()
        user.studies.add(study)
        user.save()

    resp = client.post(
        "/graphql",
        data={"query": SUBSCRIBE_TO, "variables": {"studyId": study.kf_id}},
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["subscribeTo"]["user"]["studySubscriptions"][
                "edges"
            ][0]["node"]["kfId"]
            == study.kf_id
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


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
def test_subscribe_other(db, clients, user_group, allowed):
    """
    Test that a user may or may not subscribe to a study that is not in their
    groups.

    admin - can subscribe to any study
    service - can not subscribe to studies
    user - can subscribe to any study they are in the group of
    unauthed - can not subscribe to studies
    """
    client = clients.get(user_group)

    studies = StudyFactory.create_batch(25)

    resp = client.post(
        "/graphql",
        data={
            "query": SUBSCRIBE_TO,
            "variables": {"studyId": studies[0].kf_id},
        },
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["subscribeTo"]["user"]["studySubscriptions"][
                "edges"
            ][0]["node"]["kfId"]
            == studies[0].kf_id
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_subscribe_does_not_exist(db, clients):
    """
    Test that a study that does not exist cannot be subscribed to.
    """
    client = clients.get("Administrators")
    studies = StudyFactory.create_batch(25)

    resp = client.post(
        "/graphql",
        data={"query": SUBSCRIBE_TO, "variables": {"studyId": "SD_XXXXXXXX"}},
        content_type="application/json",
    )

    assert resp.json()["errors"][0]["message"] == "Study does not exist."


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", False),
        ("Investigators", True),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_unsubscribe(db, clients, user_group, allowed):
    """
    Test that studies may be removed from a user's subscription
    """
    client = clients.get(user_group)
    studies = StudyFactory.create_batch(5)

    # Subscribe to all the studies
    group = Group.objects.filter(name=user_group).first()
    if group:
        user = group.user_set.first()
        user.studies.set(studies)
        user.study_subscriptions.set(studies)
        user.save()

    # Unsubscribe from the last study
    resp = client.post(
        "/graphql",
        data={
            "query": UNSUBSCRIBE_FROM,
            "variables": {"studyId": studies[-1].kf_id},
        },
        content_type="application/json",
    )
    if allowed:
        subs = resp.json()["data"]["unsubscribeFrom"]["user"][
            "studySubscriptions"
        ]["edges"]

        assert len(subs) == 4
        assert studies[-1].kf_id not in [s["node"]["kfId"] for s in subs]

        user = User.objects.get(
            username=resp.json()["data"]["unsubscribeFrom"]["user"]["username"]
        )
        assert user.study_subscriptions.count() == 4
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
