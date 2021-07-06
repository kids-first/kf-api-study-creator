import pytest
import uuid
from datetime import datetime
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model

from creator.tasks import setup_cavatica_task
from creator.organizations.models import Organization
from creator.organizations.factories import OrganizationFactory
from creator.users.factories import UserFactory

User = get_user_model()


ADD_MEMBER_MUTATION = """
mutation AddMember($user: ID!, $organization: ID!) {
  addMember(user: $user, organization: $organization) {
    organization {
      id
      name
      members {
        edges {
          node {
            id
            username
          }
        }
      }
    }
  }
}
"""

REMOVE_MEMBER_MUTATION = """
mutation RemoveMember($user: ID!, $organization: ID!) {
  removeMember(user: $user, organization: $organization) {
    organization {
      id
      name
      members {
        edges {
          node {
            id
            username
          }
        }
      }
    }
  }
}
"""


def test_add_member_mutation(db, permission_client):
    """
    Test that the appropriate users may add member
    """
    user, client = permission_client(["change_organization"])
    organization = OrganizationFactory()

    variables = {
        "organization": to_global_id("OrganizationNode", organization.id),
        "user": to_global_id("UserNode", user.id),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": ADD_MEMBER_MUTATION, "variables": variables},
    )

    resp_body = resp.json()["data"]["addMember"]["organization"]
    assert (
        resp_body["members"]["edges"][0]["node"]["username"]
        == user.username
    )


def test_remove_member_mutation(db, permission_client):
    """
    Test that the appropriate users may remove collaborators
    """
    user, client = permission_client(["change_organization"])
    organization = OrganizationFactory(members=[user])

    variables = {
        "organization": to_global_id("OrganizationNode", organization.id),
        "user": to_global_id("UserNode", user.id),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": REMOVE_MEMBER_MUTATION, "variables": variables},
    )

    resp_body = resp.json()["data"]["removeMember"]["organization"]
    assert len(resp_body["members"]["edges"]) == 0


def test_already_member(db, permission_client):
    """
    Test an error is thrown when trying to add a user to an organization
    they are already a member of.
    """
    user, client = permission_client(["change_organization"])
    organization = OrganizationFactory(members=[user])

    variables = {
        "organization": to_global_id("OrganizationNode", organization.id),
        "user": to_global_id("UserNode", user.id),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": ADD_MEMBER_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert "is already a member" in resp.json()["errors"][0]["message"]


def test_not_member(db, permission_client):
    """
    Test an error is thrown when trying to remove a user from an organization
    they are not a member of.
    """
    user, client = permission_client(["change_organization"])
    organization = OrganizationFactory()

    variables = {
        "organization": to_global_id("OrganizationNode", organization.id),
        "user": to_global_id("UserNode", user.id),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": REMOVE_MEMBER_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert "is not a member" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "mutation", [ADD_MEMBER_MUTATION, REMOVE_MEMBER_MUTATION]
)
def test_organization_not_found(db, clients, mutation):
    """
    Test behavior when the specified organization does not exist
    """
    client = clients.get("Administrators")
    user = UserFactory()

    variables = {
        "organization": to_global_id("OrganizationNode", uuid.uuid4()),
        "user": to_global_id("UserNode", user.id),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": mutation, "variables": variables},
    )

    assert "errors" in resp.json()
    assert "does not exist" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "mutation", [ADD_MEMBER_MUTATION, REMOVE_MEMBER_MUTATION]
)
def test_user_not_found(db, clients, mutation):
    """
    Test behavior when the specified user does not exist
    """
    client = clients.get("Administrators")
    organization = OrganizationFactory()

    variables = {
        "organization": to_global_id("OrganizationNode", organization.id),
        "user": to_global_id("UserNode", 123),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": mutation, "variables": variables},
    )

    assert "errors" in resp.json()
    assert "123 does not exist" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "mutation", [ADD_MEMBER_MUTATION, REMOVE_MEMBER_MUTATION]
)
def test_update_member_mutation_not_allowed(db, permission_client, mutation):
    """
    Users without the update_organization permission should not be allowed
    to add or remove member.
    """
    user, client = permission_client([])
    organization = OrganizationFactory()

    variables = {
        "organization": to_global_id("OrganizationNode", organization.id),
        "user": to_global_id("UserNode", user.id),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": mutation, "variables": variables},
    )

    message = resp.json()["errors"][0]["message"]
    assert "Not allowed" in message
