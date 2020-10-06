import pytest
from graphql_relay import to_global_id
from creator.{{ app_name }}.factories import {{ model_name }}Factory

{{ uppercase }} = """
query ($id: ID!) {
    {{ singular }}(id: $id) {
        id
    }
}
"""

ALL_{{ uppercase_plural }} = """
query {
    all{{ plural.title }} {
        edges { node { id } }
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
def test_query_{{ singular }}(db, clients, user_group, allowed):
    client = clients.get(user_group)

    {{ singular }} = {{ model_name }}Factory()

    variables = {"id": to_global_id("{{ model_name }}Node", {{ singular }}.id)}

    resp = client.post(
        "/graphql",
        data={"query": {{ uppercase }}, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["{{ singular }}"]["id"] == to_global_id("{{ model_name }}Node", {{ singular }}.id)
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
def test_query_all_{{ plural }}(db, clients, user_group, allowed):
    client = clients.get(user_group)

    {{ singular }} = {{ model_name }}Factory.create_batch(5)

    resp = client.post(
        "/graphql", data={"query": ALL_{{ uppercase_plural }}}, content_type="application/json"
    )

    if allowed:
        assert len(resp.json()["data"]["all{{ plural.title }}"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
