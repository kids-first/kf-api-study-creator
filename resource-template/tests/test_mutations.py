import pytest
from graphql_relay import to_global_id

from creator.{{ app_name }}.models import {{ model_name }}
from creator.{{ app_name }}.factories import {{ model_name }}Factory


CREATE_{{ uppercase }} = """
mutation ($input: Create{{ model_name }}Input!) {
    create{{ upper_camel_case }}(input: $input) {
        {{ lower_camel_case }} {
            id
        }
    }
}
"""

UPDATE_{{ uppercase }} = """
mutation ($id: ID!, $input: Update{{ upper_camel_case }}Input!) {
    update{{ upper_camel_case }}(id: $id, input: $input) {
        {{ lower_camel_case }} {
            id
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
def test_create_{{ singular }}(db, clients, user_group, allowed):
    """
    Test the create mutation.
    """
    client = clients.get(user_group)

    resp = client.post(
        "/graphql",
        data={"query": CREATE_{{ uppercase }}, "variables": {"input": {"name": "Test"}}},
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["create{{ upper_camel_case }}"][
                "{{ lower_camel_case }}"]
            is not None
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
def test_update_{{ singular }}(db, clients, user_group, allowed):
    """
    Test the update mutation.
    """
    client = clients.get(user_group)

    {{ singular }} = {{ model_name }}Factory()

    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_{{ uppercase }},
            "variables": {
                "id": to_global_id("{{ model_name }}Node}}", {{ singular }}.id),
                "input": {"name": "test"},
            },
        },
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["update{{ upper_camel_case }}"][
                "{{ lower_camel_case }}"]
            is not None
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
