import pytest
from django.contrib.auth import get_user_model
from creator.users.factories import UserFactory


@pytest.mark.parametrize(
    "user_type,email",
    [
        ("admin", "user@d3b.center"),
        ("service", None),
        ("user", "user@d3b.center"),
        (None, None),
    ],
)
def test_my_profile(
    db, admin_client, service_client, user_client, client, user_type, email
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

    query = "{ myProfile { email } }"
    resp = api_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    if email:
        assert resp.json()["data"]["myProfile"]["email"] == email
    else:
        assert (
            resp.json()["errors"][0]["message"]
            == "not authenticated as a user with a profile"
        )


@pytest.mark.parametrize(
    "field", ["password", "ego_roles", "ego_groups", "isStaff"]
)
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
