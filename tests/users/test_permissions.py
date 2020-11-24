import pytest
from graphql_relay import to_global_id
from django.contrib.auth.models import Permission


GET_PERMISSION = """
query Permission($id: ID!) {
    permission(id: $id) {
        id
        name
        codename
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
def test_all_permissions_query(db, clients, user_group, allowed):
    """
    """
    client = clients.get(user_group)

    query = "{ allPermissions { edges { node { id name codename } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    if allowed:
        assert (
            len(resp.json()["data"]["allPermissions"]["edges"])
            == Permission.objects.count()
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
def test_permission_query(db, clients, user_group, allowed):
    """
    """
    client = clients.get(user_group)
    perm = Permission.objects.first()

    resp = client.post(
        "/graphql",
        data={
            "query": GET_PERMISSION,
            "variables": {"id": to_global_id("PermissionNode", perm.id)},
        },
        content_type="application/json",
    )
    assert resp.status_code == 200
    if allowed:
        assert resp.json()["data"]["permission"]["name"] == perm.name
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_permission_query(db, clients):
    """
    Test response when a given permission is not found
    """
    client = clients.get("Administrators")

    resp = client.post(
        "/graphql",
        data={
            "query": GET_PERMISSION,
            "variables": {"id": to_global_id("PermissionNode", -99)},
        },
        content_type="application/json",
    )
    print(resp.json())
    assert resp.status_code == 200
    assert resp.json()["errors"][0]["message"] == "Permission not found"
