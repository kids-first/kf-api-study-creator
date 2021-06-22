import pytest
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model
from creator.organizations.models import Organization
from creator.organizations.factories import OrganizationFactory

User = get_user_model()

ORGANIZATION = """
query ($id: ID!) {
  organization(id: $id) {
    id
    name
  }
}
"""

ALL_ORGANIZATIONS = """
query {
    allOrganizations {
        edges { node { id name } }
    }
}
"""


def test_query_organization(db, permission_client):
    """
    Users with the 'view_organization' permission should be able to retrieve
    an organization.
    """
    user, client = permission_client(["view_organization"])
    organization = OrganizationFactory()

    variables = {"id": to_global_id("OrganizationNode", organization.pk)}
    resp = client.post(
        "/graphql",
        data={"query": ORGANIZATION, "variables": variables},
        content_type="application/json",
    )

    assert "errors" not in resp.json()
    assert resp.json()["data"]["organization"]["name"] == organization.name


def test_query_organization_not_allowed(db, permission_client):
    """
    Users without permission may not retrieve an organization.
    """
    user, client = permission_client([])
    organization = OrganizationFactory()

    variables = {"id": to_global_id("OrganizationNode", organization.pk)}
    resp = client.post(
        "/graphql",
        data={"query": ORGANIZATION, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Not allowed" in resp.json()["errors"][0]["message"]


def test_query_my_organization(db, permission_client):
    """
    Users with the 'view_my_organization' permission should be able to retrieve
    an organization if they are a member of it.
    """
    user, client = permission_client(["view_my_organization"])
    organization = OrganizationFactory(members=[user])

    variables = {"id": to_global_id("OrganizationNode", organization.pk)}
    resp = client.post(
        "/graphql",
        data={"query": ORGANIZATION, "variables": variables},
        content_type="application/json",
    )

    assert "errors" not in resp.json()
    assert resp.json()["data"]["organization"]["name"] == organization.name


def test_query_my_organization_not_a_member(db, permission_client):
    """
    Users with the 'view_my_organization' permission should not be able to
    retrieve an organization if they are not a member of it.
    """
    user, client = permission_client(["view_my_organization"])
    organization = OrganizationFactory()

    variables = {"id": to_global_id("OrganizationNode", organization.pk)}
    resp = client.post(
        "/graphql",
        data={"query": ORGANIZATION, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Not allowed" in resp.json()["errors"][0]["message"]


def test_query_all_organizations_not_allowed(db, permission_client):
    """
    Users without permissions may not list organizations.
    """
    user, client = permission_client(["view_organization"])
    organizations = OrganizationFactory.create_batch(3)

    resp = client.post(
        "/graphql",
        data={"query": ALL_ORGANIZATIONS},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Not allowed" in resp.json()["errors"][0]["message"]


def test_query_all_organizations(db, permission_client):
    """
    Users with 'list_all_organizations' may retrieve all organizations.
    """
    user, client = permission_client(["list_all_organization"])
    organizations = OrganizationFactory.create_batch(3)

    resp = client.post(
        "/graphql",
        data={"query": ALL_ORGANIZATIONS},
        content_type="application/json",
    )

    assert "errors" not in resp.json()
    assert (
        len(resp.json()["data"]["allOrganizations"]["edges"])
        == Organization.objects.count()
    )


def test_query_all_my_organizations(db, permission_client):
    """
    Users with 'view_my_organization' may retrieve only their organizations.
    """
    user, client = permission_client(["view_my_organization"])
    my_organization = OrganizationFactory(members=[user])
    other_organization = OrganizationFactory()

    resp = client.post(
        "/graphql",
        data={"query": ALL_ORGANIZATIONS},
        content_type="application/json",
    )

    assert "errors" not in resp.json()
    assert len(resp.json()["data"]["allOrganizations"]["edges"]) == 1
    assert (
        resp.json()["data"]["allOrganizations"]["edges"][0]["node"]["name"]
        == my_organization.name
    )
