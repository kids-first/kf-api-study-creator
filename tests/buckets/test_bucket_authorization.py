import pytest
from graphql_relay import to_global_id
from creator.buckets.factories import BucketFactory


@pytest.mark.parametrize("resource", ["bucket"])
@pytest.mark.parametrize(
    "user_type,expected",
    [("admin", True), ("user", False), ("other_user", False), (None, False)],
)
def test_get_node_by_id(
    db,
    admin_client,
    user_client,
    client,
    prep_file,
    resource,
    user_type,
    expected,
):
    """
    Test that resource may be retrieved by (relay) id
    - Should return resource if admin
    - Should return resource if user who is part of study
    - Should return None if user who is not part of study
    - Should return None if not an authenticated user
    """
    # Select client based on user type
    api_client = {
        "admin": admin_client,
        "user": user_client,
        "other_user": user_client,
        None: client,
    }[user_type]

    bucket = BucketFactory()
    node_id = to_global_id("BucketNode", bucket.name)

    # Now try to get node by the relay id
    query = f'{{{resource}(id: "{node_id}") {{ id }} }}'
    resp = api_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )

    assert "errors" not in resp.json()
    # Should get back the node with id if expected, None if not
    if expected:
        assert resp.json()["data"][resource]["id"] == node_id
    else:
        assert resp.json()["data"][resource] is None


@pytest.mark.parametrize("resource", ["allBuckets"])
@pytest.mark.parametrize(
    "user_type,expected",
    [("admin", True), ("user", False), ("other_user", False), (None, False)],
)
def test_get_all(
    db,
    admin_client,
    user_client,
    client,
    prep_file,
    resource,
    user_type,
    expected,
):
    """
    Test that resource may be retrieved by (relay) id
    - Should return resource if admin
    - Should return resource if user who is part of study
    - Should return None if user who is not part of study
    - Should return None if not an authenticated user
    """
    # Select client based on user type
    api_client = {
        "admin": admin_client,
        "user": user_client,
        "other_user": user_client,
        None: client,
    }[user_type]

    bucket = BucketFactory()
    node_id = to_global_id("BucketNode", bucket.name)

    # Now try to get node by the relay id
    query = f"{{{resource} {{ edges {{ node {{ id }} }} }} }}"
    resp = api_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )

    assert "errors" not in resp.json()
    # Should get back the node with id if expected, None if not
    if expected:
        assert len(resp.json()["data"][resource]["edges"]) == 1
    else:
        assert len(resp.json()["data"][resource]["edges"]) == 0
