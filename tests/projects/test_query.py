import pytest
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model
from creator.projects.factories import ProjectFactory
from creator.studies.factories import StudyFactory

User = get_user_model()

PROJECT = """
query ($id: ID!) {
    project(id: $id) {
        id
        name
    }
}
"""

ALL_PROJECTS = """
query {
    allProjects {
        edges { node { id name } }
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
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_query_project(db, clients, user_group, allowed):
    client = clients.get(user_group)

    project = ProjectFactory()
    variables = {"id": to_global_id("ProjectNode", project.project_id)}

    resp = client.post(
        "/graphql",
        data={"query": PROJECT, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["project"]["name"] == project.name
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", False),
        ("Investigators", True),
        ("Bioinformatics", True),
    ],
)
def test_query_my_project(db, clients, user_group, allowed):
    """
    Test if users may see a project that is in one of their studies
    """
    client = clients.get(user_group)

    project = ProjectFactory()
    user = User.objects.get(groups__name=user_group)
    study = StudyFactory()

    project.study = study
    project.save()
    user.studies.add(study)
    user.save()

    variables = {"id": to_global_id("ProjectNode", project.project_id)}

    resp = client.post(
        "/graphql",
        data={"query": PROJECT, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["project"]["name"] == project.name
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group,allowed,number",
    [
        ("Administrators", True, 4),
        ("Services", False, 0),
        ("Developers", False, 0),
        ("Investigators", True, 1),
        ("Bioinformatics", True, 4),
        (None, False, 0),
    ],
)
def test_query_all(db, clients, user_group, allowed, number):
    client = clients.get(user_group)
    if user_group:
        user = User.objects.get(groups__name=user_group)
        study = StudyFactory()

        projects = ProjectFactory.create_batch(4)
        projects[0].study = study
        projects[0].save()
        user.studies.add(study)
        user.save()

    resp = client.post(
        "/graphql",
        data={"query": ALL_PROJECTS},
        content_type="application/json",
    )

    if allowed:
        assert len(resp.json()["data"]["allProjects"]["edges"]) == number
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
