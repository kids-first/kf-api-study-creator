import uuid
import pytest
from graphql_relay import to_global_id
from creator.organizations.factories import OrganizationFactory
from creator.studies.factories import StudyFactory
from creator.data_templates.factories import (
    DataTemplateFactory,
    TemplateVersionFactory
)

TEMPLATE_VERSION = """
query ($id: ID!) {
    templateVersion(id: $id) {
        id
        description
        fieldDefinitions
        dataTemplate { id }
        studies { edges { node { id } } }
    }
}
"""

ALL_TEMPLATE_VERSIONS = """
query($studies: [ID]) {
allTemplateVersions(studies: $studies) {
        edges {
            node {
                id
                description
                fieldDefinitions
                dataTemplate { id }
                studies { edges { node { id kfId } } }
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
def test_query_template_version(db, permission_client, permissions, allowed):
    """
    Test templateVersion query
    """
    user, client = permission_client(permissions)
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    studies = StudyFactory.create_batch(2, organization=org)
    dt = DataTemplateFactory(organization=org)
    template_version = TemplateVersionFactory(
        data_template=dt, studies=studies
    )

    variables = {
        "id": to_global_id("TemplateVersionNode", template_version.id)
    }

    resp = client.post(
        "/graphql",
        data={"query": TEMPLATE_VERSION, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        dt = resp.json()["data"]["templateVersion"]
        assert dt["id"] == to_global_id(
            "TemplateVersionNode", template_version.id)
        for attr in [
            "description", "fieldDefinitions", "dataTemplate", "studies"
        ]:
            assert dt[attr]
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_query_template_version_missing(db, permission_client):
    """
    Test templateVersion query for a template that doesn't exist
    """
    user, client = permission_client(["view_datatemplate"])

    fake_id = str(uuid.uuid4())
    variables = {"id": to_global_id("TemplateVersionNode", fake_id)}

    resp = client.post(
        "/graphql",
        data={"query": TEMPLATE_VERSION, "variables": variables},
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
def test_query_all_template_version(
    db, permission_client, permissions, allowed
):
    """
    Test allTemplateVersions query
    """
    user, client = permission_client(permissions)
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    studies = StudyFactory.create_batch(2, organization=org)
    dt = DataTemplateFactory(organization=org)
    template_version = TemplateVersionFactory.create_batch(
        5, data_template=dt, studies=studies
    )

    resp = client.post(
        "/graphql",
        data={"query": ALL_TEMPLATE_VERSIONS},
        content_type="application/json"
    )

    if allowed:
        assert len(resp.json()["data"]["allTemplateVersions"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_filter_all_template_version(db, permission_client):
    """
    Test allTemplateVersion query with filters
    """
    user, client = permission_client(["list_all_datatemplate"])
    org = OrganizationFactory()
    dt = DataTemplateFactory(organization=org)
    template_versions = TemplateVersionFactory.create_batch(
        5, data_template=dt
    )
    study = StudyFactory(organization=org)
    for tv in template_versions[0:2]:
        tv.studies.add(study)
        tv.save()

    # Filter by study kf_id
    resp = client.post(
        "/graphql",
        data={
            "query": ALL_TEMPLATE_VERSIONS,
            "variables": {
                "studies": [to_global_id("StudyNode", study.pk)]
            },
        },
        content_type="application/json"
    )
    assert len(resp.json()["data"]["allTemplateVersions"]["edges"]) == 2
