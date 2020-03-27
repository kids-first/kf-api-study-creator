import pytest
from graphql_relay import to_global_id
from django.contrib.auth.models import Group
from creator.users.factories import UserFactory


UPDATE_USER = """
mutation UpdateUser($user: ID!, $groups: [ID]) {
    updateUser(user: $user, groups: $groups) {
        user {
            id
            groups {
                edges { node { id name } }
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
        ("Investigators", False),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_update_user_mutation(db, clients, user_group, allowed):
    """
    Test that user's may be updated with the correct permissions
    """
    client = clients.get(user_group)

    user = UserFactory()
    group = Group.objects.filter(name="Administrators").first()
    variables = {
        "user": to_global_id("UserNode", user.id),
        "groups": [to_global_id("GroupNode", group.id)],
    }

    resp = client.post(
        "/graphql",
        data={"query": UPDATE_USER, "variables": variables},
        content_type="application/json",
    )
    assert resp.status_code == 200
    if allowed:
        assert (
            len(resp.json()["data"]["updateUser"]["user"]["groups"]["edges"])
            == 1
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_user_not_found(db, clients):
    """
    Test response when the specified user does not exist
    """
    client = clients.get("Administrators")

    variables = {"user": to_global_id("UserNode", 999)}

    resp = client.post(
        "/graphql",
        data={"query": UPDATE_USER, "variables": variables},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json()["errors"][0]["message"] == "User does not exist."


def test_group_not_found(db, clients):
    """
    Test response when the specified group does not exist
    """
    client = clients.get("Administrators")

    user = UserFactory()
    variables = {
        "user": to_global_id("UserNode", user.id),
        "groups": [to_global_id("GroupNode", 999)],
    }

    resp = client.post(
        "/graphql",
        data={"query": UPDATE_USER, "variables": variables},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json()["errors"][0]["message"] == "Group does not exist."
