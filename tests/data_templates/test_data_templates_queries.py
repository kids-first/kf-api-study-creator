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
query($organization: ID, $organizationName: String) {
    allDataTemplates(organization: $organization, organizationName: $organizationName) { # noqa
        edges {
            node {
                id
                name
                description
                icon
                organization { id name }
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
        content_type="application/json",
    )

    if allowed:
        assert len(resp.json()["data"]["allDataTemplates"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_filter_all_data_template(db, permission_client):
    """
    Test allDataTemplates query with filters
    """
    user, client = permission_client(["list_all_datatemplate"])
    org = OrganizationFactory()
    data_templates = DataTemplateFactory.create_batch(5)
    for dt in data_templates[0:2]:
        dt.organization = org
        dt.save()

    # Filter by organization id
    resp = client.post(
        "/graphql",
        data={
            "query": ALL_DATA_TEMPLATES,
            "variables": {
                "organization": to_global_id("OrganizationNode", org.pk)
            },
        },
        content_type="application/json",
    )
    assert len(resp.json()["data"]["allDataTemplates"]["edges"]) == 2

    # Filter by organization name
    resp = client.post(
        "/graphql",
        data={
            "query": ALL_DATA_TEMPLATES,
            "variables": {"organizationName": org.name},
        },
        content_type="application/json",
    )
    assert len(resp.json()["data"]["allDataTemplates"]["edges"]) == 2
