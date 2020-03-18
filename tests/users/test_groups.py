import pytest
from graphql_relay import to_global_id
from django.contrib.auth.models import Group

GET_GROUP = """
query Group($id: ID!) {
    group(id: $id) {
        id
        name
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
def test_all_groups_query(db, clients, user_group, allowed):
    """
    """
    client = clients.get(user_group)

    query = "{ allGroups { edges { node { id name } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    if allowed:
        assert (
            len(resp.json()["data"]["allGroups"]["edges"])
            == Group.objects.count()
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
def test_groups_query(db, clients, user_group, allowed):
    """
    """
    client = clients.get(user_group)
    group = Group.objects.first()

    resp = client.post(
        "/graphql",
        data={
            "query": GET_GROUP,
            "variables": {"id": to_global_id("GroupNode", group.id)},
        },
        content_type="application/json",
    )
    assert resp.status_code == 200
    if allowed:
        assert resp.json()["data"]["group"]["name"] == group.name
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_groups_not_found(db, clients):
    """
    Test response when a given group is not found
    """
    client = clients.get("Administrators")

    resp = client.post(
        "/graphql",
        data={
            "query": GET_GROUP,
            "variables": {"id": to_global_id("GroupNode", 999)},
        },
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json()["errors"][0]["message"] == "Group not found"
