import pytest
import uuid
from graphql_relay import to_global_id


@pytest.mark.parametrize(
    "resource,type",
    [
        ["bucket", str],
        ["group", int],
        ["study", int],
        ["permission", int],
        ["file", int],
        ["version", int],
        ["project", int],
        ["referralToken", uuid.uuid4],
        ["release", int],
        ["releaseTask", int],
        ["releaseService", int],
        ["releaseEvent", uuid.uuid4],
    ],
)
def test_get_resource_by_id(db, clients, resource, type):
    """ Test that each resource returns the same not found response """
    client = clients.get("Administrators")
    node = resource[:1].upper() + resource[1:]
    resource_id = to_global_id(f"{node}Node", str(type()))
    # Get a node's relay id using admin client
    query = f'query getNode {{ {resource}(id: "{resource_id}") {{ id }} }}'
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )

    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"].endswith("not found")
