import pytest
from datetime import datetime
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model

from creator.tasks import setup_cavatica_task
from creator.organizations.models import Organization
from creator.organizations.factories import OrganizationFactory

User = get_user_model()


CREATE_ORGANIZATION_MUTATION = """
mutation newOrganization($input: CreateOrganizationInput!) {
    createOrganization(input: $input) {
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


def test_create_organization_mutation(db, permission_client):
    """
    Only users with add_organization should be allowed to create organizations
    """
    user, client = permission_client(["add_organization"])

    variables = {"input": {"name": "My Test DCC"}}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_ORGANIZATION_MUTATION, "variables": variables},
    )

    resp_data = resp.json()["data"]["createOrganization"]["organization"]
    assert resp_data["name"] == "My Test DCC"
    assert Organization.objects.filter(name="My Test DCC").exists()
    assert (
        Organization.objects.filter(name="My Test DCC").get().members.count()
        == 1
    )


def test_create_organization_mutation_not_allowed(db, permission_client):
    """
    Users without the add_organization permission should not be allowed to
    create organizations
    """
    user, client = permission_client([])

    variables = {"input": {"name": "My Test DCC"}}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_ORGANIZATION_MUTATION, "variables": variables},
    )

    message = resp.json()["errors"][0]["message"]
    assert "Not allowed" in message


def test_create_organization_mutation_invalid_url(db, permission_client):
    """
    Test that errors are reported when an invalid url is provided for the
    website or image field.
    """
    user, client = permission_client(["add_organization"])

    variables = {
        "input": {
            "name": "My Test DCC",
            "website": "not a url",
            "image": "fake url",
        }
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_ORGANIZATION_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    message = resp.json()["errors"][0]["message"]
    assert "'website': ['Enter a valid URL.']" in message
    assert "'image': ['Enter a valid URL.']" in message


def test_create_organization_mutation_invalid_email(db, permission_client):
    """
    Test that a valid email must be entered in the email field.
    """
    user, client = permission_client(["add_organization"])

    variables = {"input": {"name": "My Test DCC", "email": "not an email"}}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_ORGANIZATION_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    message = resp.json()["errors"][0]["message"]
    assert "'email': ['Enter a valid email address.']" in message
