import pytest
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model

from creator.tasks import setup_cavatica_task
from creator.users.factories import UserFactory
from creator.studies.models import Study
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
    "user_type,authorized,expected",
    [
        ("admin", True, True),
        ("admin", False, True),
        ("service", True, True),
        ("service", False, True),
        ("user", True, False),
        ("user", False, False),
        (None, True, False),
        (None, False, False),
    ],
)
def test_add_collaborator_mutation(
    db,
    admin_client,
    service_client,
    user_client,
    client,
    user_type,
    authorized,
    expected,
):
    """
    Only admins should be allowed to add colaborators
    """
    user = UserFactory()
    study = StudyFactory()
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "user": to_global_id("UserNode", user.sub),
    }
    resp = api_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": ADD_COLLABORATOR_MUTATION, "variables": variables},
    )

    if expected:
        resp_body = resp.json()["data"]["addCollaborator"]["study"]
        assert (
            resp_body["collaborators"]["edges"][0]["node"]["username"]
            == user.username
        )
        assert Study.objects.first().collaborators.count() == 1
    else:
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")
        assert Study.objects.first().collaborators.count() == 0


@pytest.mark.parametrize(
    "user_type,authorized,expected",
    [
        ("admin", True, True),
        ("admin", False, True),
        ("service", True, True),
        ("service", False, True),
        ("user", True, False),
        ("user", False, False),
        (None, True, False),
        (None, False, False),
    ],
)
def test_remove_collaborator_mutation(
    db,
    admin_client,
    service_client,
    user_client,
    client,
    user_type,
    authorized,
    expected,
):
    """
    Only admins should be allowed to remove colaborators
    """
    user = UserFactory()
    study = StudyFactory()
    study.collaborators.add(user)
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "user": to_global_id("UserNode", user.sub),
    }
    resp = api_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": REMOVE_COLLABORATOR_MUTATION, "variables": variables},
    )

    if expected:
        resp_body = resp.json()["data"]["removeCollaborator"]["study"]
        assert len(resp_body["collaborators"]["edges"]) == 0
        assert Study.objects.first().collaborators.count() == 0
    else:
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")
        assert Study.objects.first().collaborators.count() == 1


@pytest.mark.parametrize(
    "mutation", [ADD_COLLABORATOR_MUTATION, REMOVE_COLLABORATOR_MUTATION]
)
def test_study_not_found(db, admin_client, mutation):
    """
    Test behavior when the specified study does not exist
    """
    user = UserFactory()
    variables = {
        "study": to_global_id("StudyNode", "KF_00000000"),
        "user": to_global_id("UserNode", user.sub),
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": mutation, "variables": variables},
    )

    assert "errors" in resp.json()
    assert "KF_00000000 does not exist" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "mutation", [ADD_COLLABORATOR_MUTATION, REMOVE_COLLABORATOR_MUTATION]
)
def test_user_not_found(db, admin_client, mutation):
    """
    Test behavior when the specified user does not exist
    """
    study = StudyFactory()
    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "user": to_global_id("UserNode", "ABC"),
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": mutation, "variables": variables},
    )

    assert "errors" in resp.json()
    assert "ABC does not exist" in resp.json()["errors"][0]["message"]
