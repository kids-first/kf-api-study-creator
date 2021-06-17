import pytest
import json
import uuid
from graphql_relay import to_global_id, from_global_id
from graphql import GraphQLError

from creator.studies.models import Study
from creator.studies.factories import StudyFactory
from creator.organizations.factories import OrganizationFactory
from creator.data_templates.models import TemplateVersion
from creator.data_templates.factories import (
    DataTemplateFactory,
    TemplateVersionFactory
)
from creator.data_templates.mutations.template_version import check_studies

from pprint import pprint


CREATE_TEMPLATE_VERSION = """
mutation ($input: CreateTemplateVersionInput!) {
    createTemplateVersion(input: $input) {
        templateVersion {
            id
            description
            fieldDefinitions
            dataTemplate { id }
            studies { edges { node { id kfId } } }
        }
    }
}
"""

UPDATE_TEMPLATE_VERSION = """
mutation ($id: ID!, $input: UpdateTemplateVersionInput!) {
    updateTemplateVersion(id: $id, input: $input) {
        templateVersion {
            id
            description
            fieldDefinitions
            dataTemplate { id }
            studies { edges { node { id kfId } } }
        }
    }
}
"""


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["add_datatemplate"], True),
        ([], False),
    ],
)
def test_create_template_version(db, permission_client, permissions, allowed):
    """
    Test the create mutation

    Users without the add_datatemplate permission should not be allowed
    to create template versions
    """
    user, client = permission_client(permissions)
    org = OrganizationFactory()
    studies = StudyFactory.create_batch(2, organization=org)
    user.organizations.add(org)
    user.save()
    dt = DataTemplateFactory(organization=org)

    variables = {
        "input": {
            "fieldDefinitions": json.dumps({}),
            "description": "Added gender col to Participant Details",
            "dataTemplate": to_global_id("DataTemplateNode", dt.pk),
            "studies": [to_global_id("StudyNode", s.pk) for s in studies]
        }
    }
    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_TEMPLATE_VERSION,
            "variables": variables
        },
        content_type="application/json",
    )

    pprint(resp.json())
    if allowed:
        resp_dt = (
            resp.json()["data"]["createTemplateVersion"]["templateVersion"]
        )
        assert resp_dt is not None

        # Check creation
        _, node_id = from_global_id(resp_dt["id"])
        template_version = TemplateVersion.objects.get(pk=node_id)

        # Check attributes
        assert template_version.description == resp_dt["description"]
        fdefs = json.loads(resp_dt["fieldDefinitions"])
        assert template_version.field_definitions == fdefs
        _, dt_node = from_global_id(resp_dt["dataTemplate"]["id"])
        assert template_version.data_template.pk == dt_node

    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_create_version_missing_data_template(db, permission_client):
    """
    Test the create mutation when the data template does not exist
    """
    user, client = permission_client(["add_datatemplate"])
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    dt_id = str(uuid.uuid4())

    variables = {
        "input": {
            "fieldDefinitions": json.dumps({}),
            "description": "Added gender col to Participant Details",
            "dataTemplate": to_global_id("DataTemplateNode", dt_id),
        }
    }
    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_TEMPLATE_VERSION,
            "variables": variables
        },
        content_type="application/json",
    )

    assert f"{dt_id} does not exist" in resp.json()["errors"][0]["message"]
    assert TemplateVersion.objects.count() == 0


def test_create_template_version_not_my_org(db, permission_client):
    """
    Test the create template version for an org the user is not a member of
    """
    user, client = permission_client(["add_datatemplate"])
    org = OrganizationFactory()
    dt = DataTemplateFactory(organization=org)

    variables = {
        "input": {
            "fieldDefinitions": json.dumps({}),
            "description": "Added gender col to Participant Details",
            "dataTemplate": to_global_id("DataTemplateNode", dt.pk),
        }
    }
    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_TEMPLATE_VERSION,
            "variables": variables
        },
        content_type="application/json",
    )

    assert f"Not allowed" in resp.json()["errors"][0]["message"]
    assert TemplateVersion.objects.count() == 0


def test_create_template_version_missing_studies(db, permission_client):
    """
    Test the create template version with a study that doesn't exist
    """
    user, client = permission_client(["add_datatemplate"])
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    dt = DataTemplateFactory(organization=org)
    studies = [str(uuid.uuid4())]

    variables = {
        "input": {
            "fieldDefinitions": json.dumps({}),
            "description": "Added gender col to Participant Details",
            "dataTemplate": to_global_id("DataTemplateNode", dt.pk),
            "studies": [to_global_id("StudyNode", s) for s in studies]
        }
    }
    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_TEMPLATE_VERSION,
            "variables": variables
        },
        content_type="application/json",
    )

    assert f"Failed to create/update" in resp.json()["errors"][0]["message"]
    assert TemplateVersion.objects.count() == 0


def test_check_studies(db):
    """
    Test helper function used in template version mutations
    """
    # Study that doesn't exist should error
    node_ids = [to_global_id("StudyNode", str(uuid.uuid4()))]
    with pytest.raises(GraphQLError) as e:
        out = check_studies(node_ids)
    assert "Failed to create/update" in str(e)

    # If all studies' pk exist, return studies
    studies = StudyFactory.create_batch(2)
    node_ids = [to_global_id("StudyNode", s.pk) for s in studies]
    out = check_studies(node_ids)
    assert set(s.pk for s in out) == set(s.pk for s in studies)


def test_template_released(db):
    """
    Test TemplateVersion.released property
    """
    # TemplateVersions that have studies should have released = True
    org = OrganizationFactory()
    studies = StudyFactory.create_batch(2, organization=org)
    dt = DataTemplateFactory(organization=org)
    tv = TemplateVersionFactory(studies=studies)
    tv.refresh_from_db()
    assert tv.released == True

    # TemplateVersions that have 0 studies should have released = False
    tv.studies.set([])
    tv.save()
    assert tv.released == False


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["change_datatemplate"], True),
        ([], False),
    ],
)
def test_update_template_version(db, permission_client, permissions, allowed):
    """
    Test the update mutation

    Users without the change_datatemplate permission should not be allowed
    to update template versions
    """
    user, client = permission_client(permissions)
    # Add user to an organization
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    # Create template in organization that user is member of
    dt = DataTemplateFactory(organization=org)
    template_version = TemplateVersionFactory(data_template=dt)

    studies = StudyFactory.create_batch(2, organization=org)
    input_ = {
        "fieldDefinitions": json.dumps({"fields": []}),
        "description": "Added sex col to Participant Details",
        "studies": [to_global_id("StudyNode", s.pk) for s in studies]
    }
    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_TEMPLATE_VERSION,
            "variables": {
                "id": to_global_id("TemplateVersionNode}}", template_version.id),
                "input": input_,
            },
        },
        content_type="application/json",
    )
    template_version.refresh_from_db()

    if allowed:
        resp_dt = (
            resp.json()["data"]["updateTemplateVersion"]["templateVersion"]
        )
        assert resp_dt is not None

        # Check attributes
        assert template_version.description == resp_dt["description"]
        fdefs = json.loads(resp_dt["fieldDefinitions"])
        assert template_version.field_definitions == fdefs
        assert set([s.pk for s in studies]) == set(
            s["node"]["kfId"] for s in resp_dt["studies"]["edges"]
        )

    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_update_template_version_does_not_exist(db, permission_client):
    """
    Test the update mutation when the template version does not exist
    """
    user, client = permission_client(["change_datatemplate"])
    tv_id = str(uuid.uuid4())

    input_ = {
        "fieldDefinitions": json.dumps({"fields": []}),
        "description": "Added sex col to Participant Details",
    }
    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_TEMPLATE_VERSION,
            "variables": {
                "id": to_global_id("TemplateVersionNode}}", tv_id),
                "input": input_,
            },
        },
        content_type="application/json",
    )

    assert f"{tv_id} does not exist" in resp.json()["errors"][0]["message"]
    assert TemplateVersion.objects.count() == 0


def test_update_template_version_not_my_org(
    db, permission_client
):
    """
    Test the update template version for an org user is not a member of
    """
    user, client = permission_client(["change_datatemplate"])
    # Add user to an org
    org1 = OrganizationFactory()
    user.organizations.add(org1)
    user.save()
    # Create template in diff org
    org2 = OrganizationFactory()
    dt = DataTemplateFactory(organization=org2)
    template_version = TemplateVersionFactory(data_template=dt)

    input_ = {
        "fieldDefinitions": json.dumps({"fields": []}),
        "description": "Added sex col to Participant Details",
    }
    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_TEMPLATE_VERSION,
            "variables": {
                "id": to_global_id("TemplateVersionNode}}", template_version.id),
                "input": input_,
            },
        },
        content_type="application/json",
    )
    template_version.refresh_from_db()

    assert f"Not allowed" in resp.json()["errors"][0]["message"]


def test_update_released_template_version(db, permission_client):
    """
    Test the update template version after its already being used by studies
    """
    user, client = permission_client(["change_datatemplate"])
    # Add user to an organization
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    # Create template in organization that user is member of and assign
    # template version to some studies
    dt = DataTemplateFactory(organization=org)
    studies = StudyFactory.create_batch(2, organization=org)
    template_version = TemplateVersionFactory(
        data_template=dt, studies=studies
    )

    input_ = {
        "fieldDefinitions": json.dumps({"fields": []}),
        "description": "Added sex col to Participant Details",
    }
    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_TEMPLATE_VERSION,
            "variables": {
                "id": to_global_id("TemplateVersionNode}}", template_version.id),
                "input": input_,
            },
        },
        content_type="application/json",
    )
    template_version.refresh_from_db()

    pprint(resp.json())
    assert f"used by any studies" in resp.json()["errors"][0]["message"]
