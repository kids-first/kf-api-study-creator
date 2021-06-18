import pytest
import uuid
from graphql_relay import to_global_id, from_global_id

from creator.organizations.factories import OrganizationFactory
from creator.studies.factories import StudyFactory
from creator.data_templates.models import DataTemplate
from creator.data_templates.factories import (
    DataTemplateFactory,
    TemplateVersionFactory,
)

CREATE_DATA_TEMPLATE = """
mutation ($input: CreateDataTemplateInput!) {
    createDataTemplate(input: $input) {
        dataTemplate {
            id
            name
            description
            icon
            organization { id }
        }
    }
}
"""

UPDATE_DATA_TEMPLATE = """
mutation ($id: ID!, $input: UpdateDataTemplateInput!) {
    updateDataTemplate(id: $id, input: $input) {
        dataTemplate {
            id
            name
            description
            icon
            organization { id }
        }
    }
}
"""

DELETE_DATA_TEMPLATE = """
  mutation DeleteDataTemplate($id: ID!) {
    deleteDataTemplate(id: $id) {
      id
      success
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
def test_create_data_template(db, permission_client, permissions, allowed):
    """
    Test the create mutation

    Users without the add_datatemplate permission should not be allowed
    to create data templates
    """
    user, client = permission_client(permissions)
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()

    variables = {
        "input": {
            "name": "Participant Details",
            "description": "Participant Details",
            "icon": "ambulance",
            "organization": to_global_id("OrganizationNode", org.pk),
        }
    }
    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_DATA_TEMPLATE,
            "variables": variables
        },
        content_type="application/json",
    )

    if allowed:
        resp_dt = resp.json()["data"]["createDataTemplate"]["dataTemplate"]
        assert resp_dt is not None
        _, node_id = from_global_id(resp_dt["id"])
        data_template = DataTemplate.objects.get(pk=node_id)
        for k, v in variables["input"].items():
            if k == "organization":
                assert data_template.organization.pk == org.pk
            else:
                assert getattr(data_template, k) == v

    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_create_data_template_missing_org(db, permission_client):
    """
    Test the create mutation when organization does not exist
    """
    user, client = permission_client(["add_datatemplate"])
    org_id = str(uuid.uuid4())
    variables = {
        "input": {
            "name": "Participant Details",
            "description": "Participant Details",
            "icon": "ambulance",
            "organization": to_global_id("OrganizationNode", org_id),
        }
    }
    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_DATA_TEMPLATE,
            "variables": variables
        },
        content_type="application/json",
    )
    assert f"{org_id} does not exist" in resp.json()["errors"][0]["message"]
    assert DataTemplate.objects.count() == 0


def test_create_data_template_not_my_org(db, permission_client):
    """
    Test the create data template for an org the user is not a member of
    """
    user, client = permission_client(["add_datatemplate"])
    org = OrganizationFactory()

    variables = {
        "input": {
            "name": "Participant Details",
            "description": "Participant Details",
            "icon": "ambulance",
            "organization": to_global_id("OrganizationNode", org.pk),
        }
    }
    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_DATA_TEMPLATE,
            "variables": variables
        },
        content_type="application/json",
    )
    assert f"Not allowed" in resp.json()["errors"][0]["message"]
    assert DataTemplate.objects.count() == 0


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["change_datatemplate"], True),
        ([], False),
    ],
)
def test_update_data_template(db, permission_client, permissions, allowed):
    """
    Test the update mutation

    Users without the change_datatemplate permission should not be allowed
    to update data templates
    """
    user, client = permission_client(permissions)
    data_template = DataTemplateFactory()
    # Add user to an organization
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    # Create data template in organization that user is member of
    data_template.organization = org
    data_template.save()

    input_ = {
        "name": "Participant Details",
        "description": "Participant Details",
        "icon": "ambulance",
        "organization": to_global_id("OrganizationNode", org.pk),
    }
    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_DATA_TEMPLATE,
            "variables": {
                "id": to_global_id("DataTemplateNode}}", data_template.id),
                "input": input_,
            },
        },
        content_type="application/json",
    )

    if allowed:
        resp_dt = resp.json()["data"]["updateDataTemplate"]["dataTemplate"]
        assert resp_dt is not None
        data_template.refresh_from_db()
        for k, v in input_.items():
            if k == "organization":
                assert data_template.organization.pk == org.pk
            else:
                assert getattr(data_template, k) == v

    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_update_data_template_missing_org(db, permission_client):
    """
    Test the update mutation when the organization does not exist
    """
    user, client = permission_client(["change_datatemplate"])
    data_template = DataTemplateFactory()
    # Add user to an organization
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    # Create data template in organization that user is member of
    data_template.organization = org
    data_template.save()

    orig_name = data_template.name
    org_id = str(uuid.uuid4())

    input_ = {
        "name": "Participant Details",
        "description": "Participant Details",
        "icon": "ambulance",
        "organization": to_global_id("OrganizationNode", org_id),
    }
    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_DATA_TEMPLATE,
            "variables": {
                "id": to_global_id("DataTemplateNode}}", data_template.id),
                "input": input_,
            },
        },
        content_type="application/json",
    )

    assert f"{org_id} does not exist" in resp.json()["errors"][0]["message"]
    assert DataTemplate.objects.get(pk=data_template.pk).name == orig_name


def test_update_data_template_not_my_org(db, permission_client):
    """
    Test the update data template for an org user is not a member of
    """
    user, client = permission_client(["change_datatemplate"])
    data_template = DataTemplateFactory()
    org = OrganizationFactory()
    data_template.organization = org
    data_template.save()
    orig_name = data_template.name

    input_ = {
        "name": "Participant Details",
        "description": "Participant Details",
        "icon": "ambulance",
    }
    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_DATA_TEMPLATE,
            "variables": {
                "id": to_global_id("DataTemplateNode}}", data_template.id),
                "input": input_,
            },
        },
        content_type="application/json",
    )

    assert f"Not allowed" in resp.json()["errors"][0]["message"]
    assert DataTemplate.objects.get(pk=data_template.pk).name == orig_name


def test_update_data_template_released(db, permission_client):
    """
    Test the update mutation for template that has already been released
    """
    user, client = permission_client(["change_datatemplate"])
    # Add user to an organization
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    # Create data template in organization that user is member of
    # and assign to some studies
    studies = StudyFactory.create_batch(2, organization=org)
    data_template = DataTemplateFactory(organization=org)
    template_version = TemplateVersionFactory(
        data_template=data_template, studies=studies
    )

    input_ = {
        "name": "Participant Details",
        "description": "Participant Details",
        "icon": "ambulance",
        "organization": to_global_id("OrganizationNode", org.pk),
    }
    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_DATA_TEMPLATE,
            "variables": {
                "id": to_global_id("DataTemplateNode}}", data_template.id),
                "input": input_,
            },
        },
        content_type="application/json",
    )
    data_template.refresh_from_db()
    assert "Not allowed" in resp.json()["errors"][0]["message"]
    assert data_template.name != input_["name"]


def test_update_data_template_does_not_exist(db, permission_client):
    """
    Test the update mutation when the data template does not exist
    """
    user, client = permission_client(["change_datatemplate"])
    dt_id = str(uuid.uuid4())

    input_ = {
        "name": "Participant Details",
        "description": "Participant Details",
        "icon": "ambulance",
    }
    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_DATA_TEMPLATE,
            "variables": {
                "id": to_global_id("DataTemplateNode}}", dt_id),
                "input": input_,
            },
        },
        content_type="application/json",
    )

    assert f"{dt_id} does not exist" in resp.json()["errors"][0]["message"]
    assert DataTemplate.objects.count() == 0


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["delete_datatemplate"], True),
        ([], False),
    ],
)
def test_delete_data_template(db, permission_client, permissions, allowed):
    """
    Test the delete mutation

    Users without the delete_datatemplate permission should not be allowed
    to delete data templates
    """
    user, client = permission_client(permissions)
    # Add user to an organization
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    # Create template in organization that user is member of
    data_template = DataTemplateFactory(organization=org)

    assert DataTemplate.objects.count() == 1

    resp = client.post(
        "/graphql",
        data={
            "query": DELETE_DATA_TEMPLATE,
            "variables": {
                "id": to_global_id(
                    "DataTemplateNode}}", data_template.id
                ),
            },
        },
        content_type="application/json",
    )

    if allowed:
        resp_dt = (
            resp.json()["data"]["deleteDataTemplate"]["id"]
        )
        assert resp_dt is not None
        with pytest.raises(DataTemplate.DoesNotExist):
            DataTemplate.objects.get(id=data_template.id)

    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_delete_data_template_does_not_exist(db, permission_client):
    """
    Test the delete mutation when the data template does not exist
    """
    user, client = permission_client(["delete_datatemplate"])
    org = OrganizationFactory()
    data_template = DataTemplateFactory(organization=org)

    dt_id = str(uuid.uuid4())

    resp = client.post(
        "/graphql",
        data={
            "query": DELETE_DATA_TEMPLATE,
            "variables": {
                "id": to_global_id("DataTemplateNode}}", dt_id),
            },
        },
        content_type="application/json",
    )

    assert f"{dt_id} does not exist" in resp.json()["errors"][0]["message"]
    assert DataTemplate.objects.count() == 1


def test_delete_data_template_not_my_org(
    db, permission_client
):
    """
    Test the delete data template for an org user is not a member of
    """
    user, client = permission_client(["delete_datatemplate"])
    # Add user to an org
    org1 = OrganizationFactory()
    user.organizations.add(org1)
    user.save()
    # Create template in diff org
    org2 = OrganizationFactory()
    data_template = DataTemplateFactory(organization=org2)

    assert DataTemplate.objects.count() == 1
    resp = client.post(
        "/graphql",
        data={
            "query": DELETE_DATA_TEMPLATE,
            "variables": {
                "id": to_global_id(
                    "DataTemplateNode}}", data_template.id
                ),
            },
        },
        content_type="application/json",
    )

    assert f"Not allowed" in resp.json()["errors"][0]["message"]
    assert DataTemplate.objects.count() == 1


def test_delete_released_data_template(db, permission_client):
    """
    Test the delete data template after its already being used by studies
    """
    user, client = permission_client(["delete_datatemplate"])
    # Add user to an organization
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    studies = StudyFactory.create_batch(2, organization=org)
    # Create template in organization that user is member of
    # with a template version assigned to some studies
    data_template = DataTemplateFactory(organization=org)
    tv = TemplateVersionFactory(
        data_template=data_template, studies=studies
    )
    tv.refresh_from_db()

    assert DataTemplate.objects.count() == 1
    resp = client.post(
        "/graphql",
        data={
            "query": DELETE_DATA_TEMPLATE,
            "variables": {
                "id": to_global_id(
                    "DataTemplateNode}}", data_template.id
                ),
            },
        },
        content_type="application/json",
    )

    assert f"used by any studies" in resp.json()["errors"][0]["message"]
    assert DataTemplate.objects.count() == 1
