import uuid
import pytest
from graphql_relay import to_global_id
from creator.organizations.factories import OrganizationFactory
from creator.data_templates.factories import DataTemplateFactory

DATA_TEMPLATE = """
query ($id: ID!) {
    dataTemplate(id: $id) {
        id
        name
        description
        icon
        organization { id }
    }
}
"""

ALL_DATA_TEMPLATES = """
query {
    allDataTemplates {
        edges {
            node {
                id
                name
                description
                icon
                organization { id }
            }
        }
    }
}
"""


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["view_datatemplate"], True),
        ([], False),
    ],
)
def test_query_data_template(db, permission_client, permissions, allowed):
    """
    Test dataTemplate query
    """
    user, client = permission_client(permissions)
    org = OrganizationFactory()
    data_template = DataTemplateFactory(organization=org)
    variables = {"id": to_global_id("DataTemplateNode", data_template.id)}

    resp = client.post(
        "/graphql",
        data={"query": DATA_TEMPLATE, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        dt = resp.json()["data"]["dataTemplate"]
        assert dt["id"] == to_global_id("DataTemplateNode", data_template.id)
        for attr in ["name", "description", "icon", "organization"]:
            assert dt[attr]
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_query_data_template_missing(db, permission_client):
    """
    Test dataTemplate query for data template that doesn't exist
    """
    user, client = permission_client(["view_datatemplate"])

    fake_id = str(uuid.uuid4())
    variables = {"id": to_global_id("DataTemplateNode", fake_id)}

    resp = client.post(
        "/graphql",
        data={"query": DATA_TEMPLATE, "variables": variables},
        content_type="application/json",
    )

    assert "does not exist" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["list_all_datatemplate"], True),
        ([], False),
    ],
)
def test_query_all_data_template(db, permission_client, permissions, allowed):
    """
    Test allDataTemplates query
    """
    user, client = permission_client(permissions)
    data_template = DataTemplateFactory.create_batch(5)

    resp = client.post(
        "/graphql",
        data={"query": ALL_DATA_TEMPLATES},
        content_type="application/json"
    )

    if allowed:
        assert len(resp.json()["data"]["allDataTemplates"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
