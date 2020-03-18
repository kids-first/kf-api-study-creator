import pytest
from django.contrib.auth import get_user_model
from creator.users.factories import UserFactory


@pytest.mark.parametrize(
    "user_type,expected_count",
    [("admin", 31), ("service", 30), ("user", 1), (None, 0)],
)
def test_list_users_counts(
    db,
    admin_client,
    service_client,
    user_client,
    client,
    user_type,
    expected_count,
):
    """
    Test that the allUsers for the correct number of users returned for the
    right user types.
    Admin - List all users
    Service -List all users
    User - List only self
    Unauthed - No users
    """
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]

    users = UserFactory.create_batch(25)

    query = "{ allUsers { edges { node { username } } } }"
    resp = api_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]["allUsers"]["edges"]) == expected_count


@pytest.mark.parametrize(
    "field", ["password", "ego_roles", "ego_groups", "isStaff"]
)
def test_hidden_fields(db, admin_client, field):
    """
    Test that fields are not available
    """
    query = "{ allUsers { edges { node { " + field + " } } } }"
    resp = admin_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 400
    assert field in resp.json()["errors"][0]["message"]
