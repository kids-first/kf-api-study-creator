import pytest
from django.contrib.auth import get_user_model
from creator.users.factories import UserFactory

User = get_user_model()


UPDATE_PROFILE = """
    mutation (
        $slackNotify: Boolean,
        $slackMemberId: String,
        $emailNotify: Boolean
    ) {
        updateMyProfile(
            slackNotify: $slackNotify,
            slackMemberId: $slackMemberId
            emailNotify: $emailNotify,
        ) {
            user {
                username
                slackNotify
                slackMemberId
                emailNotify
            }
        }
    }
"""


@pytest.mark.parametrize(
    "user_type,username",
    [
        ("admin", "bobby"),
        ("service", None),
        ("user", "bobby"),
        (None, None),
    ],
)
def test_my_profile(
    db, admin_client, service_client, user_client, client, user_type, username
):
    """
    Test that the myProfile query returns correct user
    """
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]

    users = UserFactory.create_batch(25)

    query = "{ myProfile { username email } }"
    resp = api_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    if username:
        assert resp.json()["data"]["myProfile"]["username"] == username
    else:
        assert (
            resp.json()["errors"][0]["message"]
            == "not authenticated as a user with a profile"
        )


@pytest.mark.parametrize("field", ["password", "isStaff"])
def test_hidden_fields(db, admin_client, field):
    """
    Test that fields are not available
    """
    query = "{ myProfile {" + field + " } } "
    resp = admin_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 400
    assert field in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "user_type,expected",
    [("admin", True), ("service", False), ("user", True), (None, False)],
)
def test_my_profile_mutation_add_notification(
    db, admin_client, service_client, user_client, client, user_type, expected
):
    """
    Test that the myProfile query returns correct user
    """
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    """
    Test that users may update their profile with notify set to True
    """
    resp = api_client.post(
        "/graphql",
        data={
            "query": UPDATE_PROFILE,
            "variables": {
                "slackNotify": True,
                "slackMemberId": "U123TRUE",
                "emailNotify": True,
            },
        },
        content_type="application/json",
    )

    if expected:
        assert resp.json()["data"]["updateMyProfile"]["user"]["slackNotify"]
        assert resp.json()["data"]["updateMyProfile"]["user"]["emailNotify"]
        assert (
            resp.json()["data"]["updateMyProfile"]["user"]["slackMemberId"]
            == "U123TRUE"
        )
        user = User.objects.get(
            username=resp.json()["data"]["updateMyProfile"]["user"]["username"]
        )
        assert user.slack_notify
        assert user.email_notify
        assert user.slack_member_id == "U123TRUE"
    else:
        assert (
            resp.json()["errors"][0]["message"]
            == "Not authenticated to mutate profile"
        )


def test_my_profile_mutation_remove_notification(db, admin_client):
    """
    Test that users may update their profile with notify set to False
    """
    resp = admin_client.post(
        "/graphql",
        data={
            "query": UPDATE_PROFILE,
            "variables": {
                "slackNotify": False,
                "slackMemberId": "U123FALSE",
                "emailNotify": False,
            },
        },
        content_type="application/json",
    )

    assert not resp.json()["data"]["updateMyProfile"]["user"]["slackNotify"]
    assert not resp.json()["data"]["updateMyProfile"]["user"]["emailNotify"]
    assert (
        resp.json()["data"]["updateMyProfile"]["user"]["slackMemberId"]
        == "U123FALSE"
    )
    user = User.objects.get(
        username=resp.json()["data"]["updateMyProfile"]["user"]["username"]
    )
    assert not user.slack_notify
    assert not user.email_notify
    assert user.slack_member_id == "U123FALSE"
