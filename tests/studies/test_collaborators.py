import pytest
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model

from creator.tasks import setup_cavatica_task
from creator.users.factories import UserFactory
from creator.studies.models import Study, Membership
from creator.studies.factories import StudyFactory
from creator.projects.models import Project
from creator.projects.cavatica import attach_volume

User = get_user_model()


ADD_COLLABORATOR_MUTATION = """
mutation addCollaborator($study: ID!, $user: ID!) {
    addCollaborator(study: $study, user: $user) {
        study {
            kfId
            name
            collaborators { edges { node { id username } } }
        }
    }
}
"""

REMOVE_COLLABORATOR_MUTATION = """
mutation removeCollaborator($study: ID!, $user: ID!) {
    removeCollaborator(study: $study, user: $user) {
        study {
            kfId
            name
            collaborators { edges { node { id username } } }
        }
    }
}
"""


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", False),
        ("Investigators", False),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_add_collaborator_mutation(db, clients, user_group, allowed):
    """
    Test that the appropriate users may add collaborators
    """
    client = clients.get(user_group)
    user = UserFactory()
    study = StudyFactory()

    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "user": to_global_id("UserNode", user.id),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": ADD_COLLABORATOR_MUTATION, "variables": variables},
    )

    if allowed:
        resp_body = resp.json()["data"]["addCollaborator"]["study"]
        assert (
            resp_body["collaborators"]["edges"][0]["node"]["username"]
            == user.username
        )
        assert Study.objects.first().collaborators.count() == 1
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert Study.objects.first().collaborators.count() == 0


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", False),
        ("Investigators", False),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_remove_collaborator_mutation(db, clients, user_group, allowed):
    """
    Test that the appropriate users may remove collaborators
    """
    client = clients.get(user_group)
    user = UserFactory()
    study = StudyFactory()
    Membership(collaborator=user, study=study).save()

    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "user": to_global_id("UserNode", user.id),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": REMOVE_COLLABORATOR_MUTATION, "variables": variables},
    )

    if allowed:
        resp_body = resp.json()["data"]["removeCollaborator"]["study"]
        assert len(resp_body["collaborators"]["edges"]) == 0
        assert Study.objects.first().collaborators.count() == 0
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert Study.objects.first().collaborators.count() == 1


@pytest.mark.parametrize(
    "mutation", [ADD_COLLABORATOR_MUTATION, REMOVE_COLLABORATOR_MUTATION]
)
def test_study_not_found(db, clients, mutation):
    """
    Test behavior when the specified study does not exist
    """
    client = clients.get("Administrators")
    user = UserFactory()

    variables = {
        "study": to_global_id("StudyNode", "KF_00000000"),
        "user": to_global_id("UserNode", user.id),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": mutation, "variables": variables},
    )

    assert "errors" in resp.json()
    assert "KF_00000000 does not exist" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "mutation", [ADD_COLLABORATOR_MUTATION, REMOVE_COLLABORATOR_MUTATION]
)
def test_user_not_found(db, clients, mutation):
    """
    Test behavior when the specified user does not exist
    """
    client = clients.get("Administrators")
    study = StudyFactory()

    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "user": to_global_id("UserNode", 123),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": mutation, "variables": variables},
    )

    assert "errors" in resp.json()
    assert "123 does not exist" in resp.json()["errors"][0]["message"]
