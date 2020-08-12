import pytest
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model
from creator.studies.models import Membership
from creator.analyses.factories import AnalysisFactory
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory, VersionFactory

User = get_user_model()

ANALYSIS = """
query ($id: ID!) {
    analysis(id: $id) {
        id
        knownFormat
    }
}
"""

ALL_ANALYSES = """
query {
    allAnalyses {
        edges { node { id knownFormat } }
    }
}
"""


@pytest.fixture
def analysis(db):
    study = StudyFactory()
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")
    analysis = AnalysisFactory(known_format=False, version=version)
    analysis.save()

    return study, file, version, analysis


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", True),
        ("Developers", True),
        ("Investigators", False),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_query_analysis(db, clients, analysis, user_group, allowed):
    client = clients.get(user_group)

    _, _, _, analysis = analysis

    variables = {"id": to_global_id("AnalysisNode", analysis.id)}

    resp = client.post(
        "/graphql",
        data={"query": ANALYSIS, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["analysis"]["knownFormat"] is False
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", True),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
    ],
)
def test_query_my_analysis(db, clients, analysis, user_group, allowed):
    """
    Test if users may see an analysis that is in one of their studies
    """
    client = clients.get(user_group)

    user = User.objects.get(groups__name=user_group)
    study, file, version, analysis = analysis
    Membership(collaborator=user, study=study).save()

    variables = {"id": to_global_id("AnalysisNode", analysis.id)}

    resp = client.post(
        "/graphql",
        data={"query": ANALYSIS, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["analysis"]["knownFormat"] is False
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group,allowed,number",
    [
        ("Administrators", True, 1),
        ("Services", False, 0),
        ("Developers", False, 0),
        ("Investigators", True, 1),
        ("Bioinformatics", False, 0),
        (None, False, 0),
    ],
)
def test_query_all(db, clients, user_group, allowed, number):
    client = clients.get(user_group)
    study = StudyFactory()
    file = FileFactory(study=study)
    AnalysisFactory.create_batch(4, version=file.versions.first())

    if user_group:
        user = User.objects.get(groups__name=user_group)
        Membership(collaborator=user, study=study).save()

    resp = client.post(
        "/graphql",
        data={"query": ALL_ANALYSES},
        content_type="application/json",
    )

    if allowed:
        assert len(resp.json()["data"]["allAnalyses"]["edges"]) == number
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
