import uuid

import pytest
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model

from creator.studies.factories import StudyFactory
from creator.storage_analyses.factories.factory import StorageAnalysisFactory

User = get_user_model()

STORAGE_ANALYSIS = """
query ($id: ID!) {
    storageAnalysis(id: $id) {
        id
        createdAt
        refreshedAt
        stats
        study { id }
    }
}
"""

ALL_STORAGE_ANALYSES = """
query {
    allStorageAnalyses { # noqa
        edges {
            node {
                id
                createdAt
                refreshedAt
                stats
                study { id }
            }
        }
    }
}
"""


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", True),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_view_storage_analyses_by_role(db, clients, user_group, allowed):
    """
    Test StorageAnalysis query
    """
    client = clients.get(user_group)
    study = StudyFactory()
    if user_group:
        user = User.objects.filter(groups__name=user_group).first()
        user.studies.add(study)
        user.save()
    storage_analysis = StorageAnalysisFactory(study=study)
    variables = {
        "id": to_global_id("StorageAnalysisNode", storage_analysis.id)
    }

    resp = client.post(
        "/graphql",
        data={"query": STORAGE_ANALYSIS, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        dt = resp.json()["data"]["storageAnalysis"]
        assert dt["id"] == to_global_id(
            "StorageAnalysisNode", storage_analysis.id)
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["view_storageanalysis"], True),
        ([], False),
    ],
)
def test_query_storage_analysis(db, permission_client, permissions, allowed):
    """
    Test storageAnalysis query
    """
    user, client = permission_client(permissions)
    study = StudyFactory()
    user.studies.add(study)
    user.save()
    storage_analysis = StorageAnalysisFactory(study=study)
    variables = {
        "id": to_global_id("StorageAnalysisNode", storage_analysis.id)
    }
    resp = client.post(
        "/graphql",
        data={"query": STORAGE_ANALYSIS, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        dt = resp.json()["data"]["storageAnalysis"]
        assert dt["id"] == to_global_id(
            "StorageAnalysisNode", storage_analysis.id)
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_query_storage_analysis_missing(db, permission_client):
    """
    Test storageAnalysis query for data template that doesn't exist
    """
    user, client = permission_client(["view_storageanalysis"])

    fake_id = str(uuid.uuid4())
    variables = {"id": to_global_id("StorageAnalysisNode", fake_id)}

    resp = client.post(
        "/graphql",
        data={"query": STORAGE_ANALYSIS, "variables": variables},
        content_type="application/json",
    )

    assert "does not exist" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["list_all_storageanalysis"], True),
        ([], False),
    ],
)
def test_query_all_storage_analysis(
    db, permission_client, permissions, allowed
):
    """
    Test allStorageAnalyses query
    """
    user, client = permission_client(permissions)
    study = StudyFactory()
    user.studies.add(study)
    user.save()
    storage_analysis = StorageAnalysisFactory.create_batch(5, study=study)

    resp = client.post(
        "/graphql",
        data={"query": ALL_STORAGE_ANALYSES},
        content_type="application/json",
    )

    if allowed:
        assert len(resp.json()["data"]["allStorageAnalyses"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


# def test_filter_all_storage_analysis(db, permission_client):
#     """
#     Test allStorageAnalyses query with filters
#     """
#     user, client = permission_client(["list_all_storageanalysis"])
#     org = OrganizationFactory()
#     storage_analyses = StorageAnalysisFactory.create_batch(5)
#     for dt in storage_analyses[0:2]:
#         dt.organization = org
#         dt.save()

#     # Filter by organization id
#     resp = client.post(
#         "/graphql",
#         data={
#             "query": ALL_STORAGE_ANALYSES,
#             "variables": {
#                 "organization": to_global_id("OrganizationNode", org.pk)
#             },
#         },
#         content_type="application/json",
#     )
#     assert len(resp.json()["data"]["allStorageAnalyses"]["edges"]) == 2

#     # Filter by organization name
#     resp = client.post(
#         "/graphql",
#         data={
#             "query": ALL_STORAGE_ANALYSES,
#             "variables": {"organizationName": org.name},
#         },
#         content_type="application/json",
#     )
#     assert len(resp.json()["data"]["allStorageAnalyses"]["edges"]) == 2
