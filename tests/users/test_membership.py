from graphql_relay import to_global_id
from django.contrib.auth import get_user_model
from creator.studies.models import Membership
from creator.studies.factories import StudyFactory
from creator.users.factories import UserFactory


GET_COLLABS = """
query collabs($study: ID!) {
  study(id: $study) {
    kfId
    collaborators {
      edges {
        invitedBy {
          username
          email
        }
        joinedOn
        role
        node {
          username
          email
        }
      }
    }
  }
}
"""


def test_collaborator_edges(db, clients):
    """
    Test that collaborator edges have additional properties
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    u1 = UserFactory()
    Membership(study=study, collaborator=u1).save()
    u2 = UserFactory()
    Membership(study=study, collaborator=u2, role="ADMIN").save()

    resp = client.post(
        "/graphql",
        data={
            "query": GET_COLLABS,
            "variables": {"study": to_global_id("StudyNode", study.kf_id)},
        },
        content_type="application/json",
    )
    assert resp.status_code == 200
    edges = resp.json()["data"]["study"]["collaborators"]["edges"]
    assert len(edges) == 2
    for edge in edges:
        assert all(e in edge for e in ["joinedOn", "role", "invitedBy"])
