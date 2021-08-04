import pytest
import uuid
from graphql_relay import to_global_id

from django.contrib.auth import get_user_model
from creator.organizations.factories import OrganizationFactory
from creator.organizations.models import Organization
from creator.users.factories import UserFactory

User = get_user_model()

ALL_USERS_ORGANIZATION = """
query ($organization: ID) {
  allUsers (organization: $organization){
    edges {
      node {
        id
        organizations {
          edges {
            node {
              id
              name
            }
          }
        }
      }
    }
  }
}
"""


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["list_all_user"], True),
        ([], False),
    ],
)
def test_query_all_users_organization(
    db, permission_client, permissions, allowed
):
    """
    Test the allUsers query for filtering by organization name functionality.
    """
    user, client = permission_client(permissions)

    # Setup users and organizations
    org1, org2, org3 = OrganizationFactory.create_batch(3)

    user1, user2, user3, *_ = UserFactory.create_batch(13)

    user1.organizations.set([org1])
    user1.save()
    user2.organizations.set([org1, org2])
    user2.save()
    user3.organizations.set([org1, org2, org3])
    user3.save()

    variables = {"organization": to_global_id("OrganizationNode", org2.pk)}
    resp = client.post(
        "/graphql",
        data={"query": ALL_USERS_ORGANIZATION, "variables": variables},
        content_type="application/json",
    )

    # Check that user2 and user3 are returned as they both have org2
    results = resp.json()["data"]["allUsers"]["edges"]
    if allowed:
        assert len(results) == 2
        node_ids = [node["node"]["id"] for node in results]
        for user in (user2, user3):
            assert to_global_id("UserNode", user.pk) in node_ids
    else:
        # When not allowed, no errors occur. An empty list is returned.
        assert not results


def test_query_all_users_fake_org(db, permission_client):
    """
    Test that the allUsers query when filtering by an organization that
    doesn't exist raises an error.
    """
    user, client = permission_client(["list_all_user"])

    org1, org2 = OrganizationFactory.create_batch(2)

    user1, user2, *_ = UserFactory.create_batch(12)

    user1.organizations.set([org1])
    user1.save()
    user2.organizations.set([org1, org2])
    user2.save()

    fake_id = str(uuid.uuid4())
    # An org is created by permission client, check them all
    for org in Organization.objects.all():
        assert fake_id != org.pk

    variables = {"organization": fake_id}
    resp = client.post(
        "/graphql",
        data={"query": ALL_USERS_ORGANIZATION, "variables": variables},
        content_type="application/json",
    )

    assert "Invalid ID" in resp.json()["errors"][0]["message"]
