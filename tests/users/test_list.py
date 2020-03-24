import pytest
from creator.models import User
from creator.users.factories import UserFactory


@pytest.mark.parametrize(
    "user_group,expected",
    [
        ("Administrators", lambda: User.objects.count()),
        ("Services", 1),
        ("Developers", 1),
        ("Investigators", 1),
        ("Bioinformatics", 1),
        (None, 0),
    ],
)
def test_list_users_counts(transactional_db, clients, user_group, expected):
    """
    Test that the allUsers for the correct number of users returned for the
    right user types.
    Only admins may list all users. Everyone else will only be returned their
    user.
    """
    client = clients.get(user_group)

    users = UserFactory.create_batch(25)

    query = "{ allUsers { edges { node { username } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    if callable(expected):
        expected = expected()
    assert len(resp.json()["data"]["allUsers"]["edges"]) == expected


@pytest.mark.parametrize(
    "field", ["password", "ego_roles", "ego_groups", "isStaff"]
)
def test_hidden_fields(db, clients, field):
    """
    Test that fields are not available
    """
    client = clients.get("Administrators")
    query = "{ allUsers { edges { node { " + field + " } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 400
    assert field in resp.json()["errors"][0]["message"]
