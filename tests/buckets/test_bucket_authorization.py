import pytest
from graphql_relay import to_global_id
from creator.buckets.factories import BucketFactory


@pytest.mark.parametrize("resource", ["bucket"])
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
def test_get_node_by_id(db, clients, prep_file, resource, user_group, allowed):
    """
    Test that resource may or may not be retrieved by (relay) id
    """
    # Select client based on user type
    client = clients.get(user_group)

    bucket = BucketFactory()
    node_id = to_global_id("BucketNode", bucket.name)

    # Now try to get node by the relay id
    query = f'{{{resource}(id: "{node_id}") {{ id }} }}'
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )

    # Should get back the node with id if expected, None if not
    if allowed:
        assert resp.json()["data"][resource]["id"] == node_id
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize("resource", ["allBuckets"])
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
def test_get_all(db, clients, prep_file, resource, user_group, allowed):
    """
    Test that resource may or may not be retrieved by (relay) id
    """
    # Select client based on user type
    client = clients.get(user_group)

    bucket = BucketFactory()

    # Now try to get node by the relay id
    query = f"{{{resource} {{ edges {{ node {{ id }} }} }} }}"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )

    # Should get back the node with id if expected, None if not
    if allowed:
        assert len(resp.json()["data"][resource]["edges"]) == 1
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
