import pytest
import uuid
from datetime import datetime
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model

from creator.tasks import setup_cavatica_task
from creator.organizations.models import Organization
from creator.organizations.factories import OrganizationFactory

User = get_user_model()


UPDATE_ORGANIZATION_MUTATION = """
mutation updateOrganization($id: ID!, $input: UpdateOrganizationInput!) {
    updateOrganization(id: $id, input: $input) {
        organization {
            name
            description
            createdOn
            website
            email
            members { edges { node { id username } } }
        }
    }
}
"""


def test_update_organization_mutation(db, permission_client):
    """
    Only users with the change_organization permission may update an
    organization entity.
    """
    user, client = permission_client(["change_organization"])

    organization = OrganizationFactory(members=[user])
    variables = {
        "id": to_global_id("OrganizationNode", organization.id),
        "input": {"name": "New Name"},
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_ORGANIZATION_MUTATION, "variables": variables},
    )

    resp_data = resp.json()["data"]["updateOrganization"]["organization"]
    assert resp_data["name"] == "New Name"


def test_update_organization_mutation_not_allowed(db, permission_client):
    """
    Users without the update_organization permission should not be allowed
    to update an organization entity.
    """
    user, client = permission_client([])

    organization = OrganizationFactory()
    variables = {
        "id": to_global_id("OrganizationNode", organization.id),
        "input": {"name": "New Name"},
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_ORGANIZATION_MUTATION, "variables": variables},
    )

    message = resp.json()["errors"][0]["message"]
    assert "Not allowed" in message


def test_update_organization_mutation_does_not_exist(db, permission_client):
    """
    Test that an organization must exist to be updated
    """
    user, client = permission_client(["change_organization"])

    organization = OrganizationFactory()
    variables = {
        "id": to_global_id("OrganizationNode", uuid.uuid4()),
        "input": {"name": "New Name"},
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_ORGANIZATION_MUTATION, "variables": variables},
    )

    message = resp.json()["errors"][0]["message"]
    assert "does not exist" in message


def test_update_organization_mutation_invalid_url(db, permission_client):
    """
    Test that errors are reported when an invalid url is provided for the
    website or image field.
    """
    user, client = permission_client(["change_organization"])

    organization = OrganizationFactory()
    variables = {
        "id": to_global_id("OrganizationNode", organization.id),
        "input": {
            "name": "My Test DCC",
            "website": "not a url",
            "image": "fake url",
        },
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_ORGANIZATION_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    message = resp.json()["errors"][0]["message"]
    assert "'website': ['Enter a valid URL.']" in message
    assert "'image': ['Enter a valid URL.']" in message


def test_update_organization_mutation_invalid_email(db, permission_client):
    """
    Test that a valid email must be entered in the email field.
    """
    user, client = permission_client(["change_organization"])

    organization = OrganizationFactory()
    variables = {
        "id": to_global_id("OrganizationNode", organization.id),
        "input": {"name": "My Test DCC", "email": "not an email"},
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_ORGANIZATION_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    message = resp.json()["errors"][0]["message"]
    assert "'email': ['Enter a valid email address.']" in message
