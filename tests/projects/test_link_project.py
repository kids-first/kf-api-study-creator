import pytest
from graphql_relay import to_global_id

from creator.studies.models import Study
from creator.studies.factories import StudyFactory

from creator.projects.models import Project
from creator.projects.factories import ProjectFactory


LINK_PROJECT = """
mutation ($study: ID!, $project: ID!) {
    linkProject(study: $study, project: $project) {
        study {
            id
            kfId
            projects { edges { node { id projectId } } }
        }
    }
}
"""

UNLINK_PROJECT = """
mutation ($study: ID!, $project: ID!) {
    unlinkProject(study: $study, project: $project) {
        study {
            id
            kfId
            projects { edges { node { id projectId } } }
        }
        project {
            id
            projectId
            study { id kfId }
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
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_link_project(db, clients, user_group, allowed):
    """
    Test that only admins may link a project to a study
    """
    client = clients.get(user_group)

    study = StudyFactory()
    project = ProjectFactory()

    resp = client.post(
        "/graphql",
        data={
            "query": LINK_PROJECT,
            "variables": {
                "study": to_global_id("StudyNode", study.kf_id),
                "project": to_global_id("ProjectNode", project.project_id),
            },
        },
        content_type="application/json",
    )

    if allowed:
        assert (
            len(
                resp.json()["data"]["linkProject"]["study"]["projects"][
                    "edges"
                ]
            )
            == 1
        )
        assert Project.objects.first().study == study
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert Project.objects.first().study is None


def test_double_link_project(db, clients):
    """
    Test that linking a project again does not remove or change a link
    """
    client = clients.get("Administrators")

    study = StudyFactory()
    project = ProjectFactory()

    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "project": to_global_id("ProjectNode", project.project_id),
    }

    assert Project.objects.first().study is None

    # Link once
    resp = client.post(
        "/graphql",
        data={"query": LINK_PROJECT, "variables": variables},
        content_type="application/json",
    )
    assert (
        len(resp.json()["data"]["linkProject"]["study"]["projects"]["edges"])
        == 1
    )
    assert Project.objects.first().study == study

    # Link again
    resp = client.post(
        "/graphql",
        data={"query": LINK_PROJECT, "variables": variables},
        content_type="application/json",
    )
    assert (
        len(resp.json()["data"]["linkProject"]["study"]["projects"]["edges"])
        == 1
    )
    assert Project.objects.first().study == study


@pytest.mark.parametrize("query", [LINK_PROJECT, UNLINK_PROJECT])
def test_project_does_not_exist(db, clients, query):
    """
    Test that a project cannot be (un)linked if it doesn't exist
    """
    client = clients.get("Administrators")

    study = StudyFactory()

    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "project": "blah",
    }

    resp = client.post(
        "/graphql",
        data={"query": query, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Project does not exist" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize("query", [LINK_PROJECT, UNLINK_PROJECT])
def test_study_does_not_exist(db, clients, query):
    """
    Test that a project cannot be (un)linked if it the study doesn't exist
    """
    client = clients.get("Administrators")

    project = ProjectFactory()

    variables = {
        "study": "blah",
        "project": to_global_id("ProjectNode", project.project_id),
    }

    resp = client.post(
        "/graphql",
        data={"query": query, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Study does not exist" in resp.json()["errors"][0]["message"]


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
def test_unlink_project(db, clients, user_group, allowed):
    """
    Test that only admins may unlink a project
    """
    client = clients.get(user_group)
    study = StudyFactory()
    project = ProjectFactory()
    project.study = study
    project.save()

    assert Project.objects.first().study == study

    resp = client.post(
        "/graphql",
        data={
            "query": UNLINK_PROJECT,
            "variables": {
                "study": to_global_id("StudyNode", study.kf_id),
                "project": to_global_id("ProjectNode", project.project_id),
            },
        },
        content_type="application/json",
    )

    if allowed:
        assert (
            len(
                resp.json()["data"]["unlinkProject"]["study"]["projects"][
                    "edges"
                ]
            )
            == 0
        )
        assert resp.json()["data"]["unlinkProject"]["project"]["study"] is None
        assert Project.objects.first().study is None
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert Project.objects.first().study == study


def test_unlink_project_no_link(db, clients):
    """
    Test that unlinking a project that isn't linked doesn't change anything
    """
    client = clients.get("Administrators")

    study = StudyFactory()
    project = ProjectFactory()

    assert Project.objects.first().study is None

    resp = client.post(
        "/graphql",
        data={
            "query": UNLINK_PROJECT,
            "variables": {
                "study": to_global_id("StudyNode", study.kf_id),
                "project": to_global_id("ProjectNode", project.project_id),
            },
        },
        content_type="application/json",
    )

    assert (
        len(resp.json()["data"]["unlinkProject"]["study"]["projects"]["edges"])
        == 0
    )
    assert resp.json()["data"]["unlinkProject"]["project"]["study"] is None
    assert Project.objects.first().study is None
