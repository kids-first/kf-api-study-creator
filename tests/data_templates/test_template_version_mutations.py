import pytest
import json
import uuid
from graphql_relay import to_global_id, from_global_id
from graphql import GraphQLError

from creator.studies.factories import StudyFactory
from creator.organizations.factories import OrganizationFactory
from creator.data_templates.models import TemplateVersion
from creator.data_templates.factories import (
    DataTemplateFactory,
    TemplateVersionFactory,
)
from creator.data_templates.mutations.template_version import check_studies


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

DELETE_TEMPLATE_VERSION = """
  mutation DeleteTemplateVersion($id: ID!) {
    deleteTemplateVersion(id: $id) {
      id
      success
    }
  }
"""


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["add_datatemplate", "change_study"], True),
        (["add_datatemplate"], False),
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
    user.studies.set(studies)
    user.save()
    dt = DataTemplateFactory(organization=org)

    variables = {
        "input": {
            "fieldDefinitions": json.dumps({}),
            "description": "Added gender col to Participant Details",
            "dataTemplate": to_global_id("DataTemplateNode", dt.pk),
            "studies": [to_global_id("StudyNode", s.pk) for s in studies],
        }
    }
    resp = client.post(
        "/graphql",
        data={"query": CREATE_TEMPLATE_VERSION, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        resp_dt = resp.json()["data"]["createTemplateVersion"][
            "templateVersion"
        ]
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
        assert "Not allowed" in resp.json()["errors"][0]["message"]


def test_create_and_apply_all(db, permission_client):
    """
    Test create and add template to all studies in org
    """
    user, client = permission_client(["add_datatemplate", "change_study"])
    org = OrganizationFactory()
    studies = StudyFactory.create_batch(3, organization=org)
    user.organizations.add(org)
    user.studies.set(studies)
    user.save()
    dt = DataTemplateFactory(organization=org)

    variables = {
        "input": {
            "fieldDefinitions": json.dumps({}),
            "description": "Added gender col to Participant Details",
            "dataTemplate": to_global_id("DataTemplateNode", dt.pk),
            # User accidentally supplied both these inputs
            # Should result in apply all behavior
            "applyToAll": True,
            "studies": [to_global_id("StudyNode", studies[0].pk)],
        }
    }
    resp = client.post(
        "/graphql",
        data={"query": CREATE_TEMPLATE_VERSION, "variables": variables},
        content_type="application/json",
    )

    # Check creation
    resp_dt = resp.json()["data"]["createTemplateVersion"]["templateVersion"]
    assert resp_dt is not None
    _, node_id = from_global_id(resp_dt["id"])
    tv = TemplateVersion.objects.get(pk=node_id)
    assert set(s.pk for s in tv.studies.all()) == set(
        s.pk for s in org.studies.all()
    )


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
        data={"query": CREATE_TEMPLATE_VERSION, "variables": variables},
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
        data={"query": CREATE_TEMPLATE_VERSION, "variables": variables},
        content_type="application/json",
    )

    assert "Not allowed" in resp.json()["errors"][0]["message"]
    assert TemplateVersion.objects.count() == 0


def test_create_template_version_missing_studies(db, permission_client):
    """
    Test the create template version with a study that doesn't exist
    """
    user, client = permission_client(["add_datatemplate", "change_study"])
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
            "studies": [to_global_id("StudyNode", s) for s in studies],
        }
    }
    resp = client.post(
        "/graphql",
        data={"query": CREATE_TEMPLATE_VERSION, "variables": variables},
        content_type="application/json",
    )

    assert "Failed to create/update" in resp.json()["errors"][0]["message"]
    assert TemplateVersion.objects.count() == 0


def test_check_studies(db):
    """
    Test helper function used in template version mutations
    """

    class MockUser:
        def __init__(self, perms=[]):
            self.perms = perms

        def has_perm(self, perm):
            return perm in set(self.perms)

    studies = StudyFactory.create_batch(4)

    # User doesn't have change study permission
    user = MockUser()
    node_ids = [to_global_id("StudyNode", s.pk) for s in studies]
    with pytest.raises(GraphQLError) as e:
        check_studies(node_ids, user)
    assert "Not allowed" in str(e)

    # Study that doesn't exist should error
    user = MockUser(perms=["studies.change_study"])
    node_ids = [to_global_id("StudyNode", str(uuid.uuid4()))]
    with pytest.raises(GraphQLError) as e:
        check_studies(node_ids, user)
    assert "Failed to create/update" in str(e)

    # If all studies' pk exist and user allowed to modify, return studies
    study_ids = [s.pk for s in studies]
    out = check_studies(study_ids, user, primary_keys=True)
    assert set(s.pk for s in out) == set(study_ids)


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
    assert tv.released == True  # noqa

    # TemplateVersions that have 0 studies should have released = False
    tv.studies.set([])
    tv.save()
    assert tv.released == False  # noqa


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["change_datatemplate", "change_study"], True),
        (["change_datatemplate"], False),
        ([], False),
    ],
)
def test_update_template_version(db, permission_client, permissions, allowed):
    """
    Test the update mutation

    Users without the change_datatemplate permission should not be allowed
    to update template versions
    """
    # Create a user that is a member of an org and some studies
    user, client = permission_client(permissions)
    org = OrganizationFactory()
    studies = StudyFactory.create_batch(2, organization=org)
    user.studies.set(studies)
    user.organizations.add(org)
    user.save()
    # Create template in organization that user is member of
    dt = DataTemplateFactory(organization=org)
    template_version = TemplateVersionFactory(data_template=dt)

    input_ = {
        "fieldDefinitions": json.dumps({"fields": []}),
        "description": "Added sex col to Participant Details",
        "studies": [to_global_id("StudyNode", s.pk) for s in studies],
    }
    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_TEMPLATE_VERSION,
            "variables": {
                "id": to_global_id("TemplateVersionNode", template_version.id),
                "input": input_,
            },
        },
        content_type="application/json",
    )
    template_version.refresh_from_db()

    if allowed:
        resp_dt = resp.json()["data"]["updateTemplateVersion"][
            "templateVersion"
        ]
        assert resp_dt is not None

        # Check attributes
        assert template_version.description == resp_dt["description"]
        fdefs = json.loads(resp_dt["fieldDefinitions"])
        assert template_version.field_definitions == fdefs
        assert set([s.pk for s in studies]) == set(
            s["node"]["kfId"] for s in resp_dt["studies"]["edges"]
        )

    else:
        assert "Not allowed" in resp.json()["errors"][0]["message"]


def test_update_and_apply_all(db, permission_client):
    """
    Test update and add template to all studies in org
    """
    # Create a user that is a member of an org and some studies
    user, client = permission_client(["change_datatemplate", "change_study"])
    org = OrganizationFactory()
    studies = StudyFactory.create_batch(2, organization=org)
    user.studies.set(studies)
    user.organizations.add(org)
    user.save()
    # Create template in organization that user is member of
    dt = DataTemplateFactory(organization=org)
    tv = TemplateVersionFactory(data_template=dt)

    input_ = {
        "fieldDefinitions": json.dumps({}),
        "description": "Added gender col to Participant Details",
        # User accidentally supplied both these inputs
        # Should result in apply all behavior
        "applyToAll": True,
        "studies": [to_global_id("StudyNode", studies[0].pk)],
    }
    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_TEMPLATE_VERSION,
            "variables": {
                "id": to_global_id("TemplateVersionNode", tv.id),
                "input": input_,
            },
        },
        content_type="application/json",
    )
    tv.refresh_from_db()

    # Check update
    resp_dt = resp.json()["data"]["updateTemplateVersion"]["templateVersion"]
    assert resp_dt is not None
    assert set(s.pk for s in tv.studies.all()) == set(
        s.pk for s in org.studies.all()
    )


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
                "id": to_global_id("TemplateVersionNode", tv_id),
                "input": input_,
            },
        },
        content_type="application/json",
    )

    assert f"{tv_id} does not exist" in resp.json()["errors"][0]["message"]
    assert TemplateVersion.objects.count() == 0


def test_update_template_version_not_my_org(db, permission_client):
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
                "id": to_global_id("TemplateVersionNode", template_version.id),
                "input": input_,
            },
        },
        content_type="application/json",
    )
    template_version.refresh_from_db()

    assert "Not allowed" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["delete_datatemplate"], True),
        ([], False),
    ],
)
def test_delete_template_version(db, permission_client, permissions, allowed):
    """
    Test the delete mutation

    Users without the delete_datatemplate permission should not be allowed
    to delete template versions
    """
    user, client = permission_client(permissions)
    # Add user to an organization
    org = OrganizationFactory()
    user.organizations.add(org)
    user.save()
    # Create template in organization that user is member of
    dt = DataTemplateFactory(organization=org)
    template_version = TemplateVersionFactory(data_template=dt)

    assert TemplateVersion.objects.count() == 1

    resp = client.post(
        "/graphql",
        data={
            "query": DELETE_TEMPLATE_VERSION,
            "variables": {
                "id": to_global_id("TemplateVersionNode", template_version.id),
            },
        },
        content_type="application/json",
    )

    if allowed:
        resp_dt = resp.json()["data"]["deleteTemplateVersion"]["id"]
        assert resp_dt is not None
        with pytest.raises(TemplateVersion.DoesNotExist):
            TemplateVersion.objects.get(id=template_version.id)

    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_delete_template_version_does_not_exist(db, permission_client):
    """
    Test the delete mutation when the template version does not exist
    """
    user, client = permission_client(["delete_datatemplate"])
    org = OrganizationFactory()
    dt = DataTemplateFactory(organization=org)
    template_version = TemplateVersionFactory(data_template=dt)

    tv_id = str(uuid.uuid4())

    resp = client.post(
        "/graphql",
        data={
            "query": DELETE_TEMPLATE_VERSION,
            "variables": {
                "id": to_global_id("TemplateVersionNode", tv_id),
            },
        },
        content_type="application/json",
    )

    assert f"{tv_id} does not exist" in resp.json()["errors"][0]["message"]
    assert TemplateVersion.objects.count() == 1


def test_delete_template_version_not_my_org(db, permission_client):
    """
    Test the delete template version for an org user is not a member of
    """
    user, client = permission_client(["delete_datatemplate"])
    # Add user to an org
    org1 = OrganizationFactory()
    user.organizations.add(org1)
    user.save()
    # Create template in diff org
    org2 = OrganizationFactory()
    dt = DataTemplateFactory(organization=org2)
    template_version = TemplateVersionFactory(data_template=dt)

    assert TemplateVersion.objects.count() == 1
    resp = client.post(
        "/graphql",
        data={
            "query": DELETE_TEMPLATE_VERSION,
            "variables": {
                "id": to_global_id("TemplateVersionNode", template_version.id),
            },
        },
        content_type="application/json",
    )

    assert "Not allowed" in resp.json()["errors"][0]["message"]
    assert TemplateVersion.objects.count() == 1


def test_delete_released_template_version(db, permission_client):
    """
    Test the delete template version after it's already being used by studies
    """
    user, client = permission_client(["delete_datatemplate"])
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

    assert TemplateVersion.objects.count() == 1
    resp = client.post(
        "/graphql",
        data={
            "query": DELETE_TEMPLATE_VERSION,
            "variables": {
                "id": to_global_id("TemplateVersionNode", template_version.id),
            },
        },
        content_type="application/json",
    )

    assert "used by any studies" in resp.json()["errors"][0]["message"]
    assert TemplateVersion.objects.count() == 1
