from pprint import pprint
import pytest
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model
from creator.studies.models import Membership
from creator.ingest_runs.factories import ValidationRunFactory
from pprint import pprint

User = get_user_model()

VALIDATION_RUN = """
query ($id: ID!) {
    validationRun(id: $id) {
        id
        inputHash
        success
        progress
        dataReview { id kfId }
    }
}
"""

ALL_VALIDATION_RUNS = """
query {
    allValidationRuns {
     edges {
       node {
         id
         inputHash
         success
         progress
         dataReview { id kfId }
       }
     }
  }
}
"""


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_query_validation_run(db, clients, data_review, user_group, allowed):
    client = clients.get(user_group)
    if user_group:
        user = User.objects.filter(groups__name=user_group).first()
        Membership(collaborator=user, study=data_review.study).save()

    validation_run = ValidationRunFactory(data_review=data_review)
    variables = {"id": to_global_id("ValidationRunNode", validation_run.id)}

    resp = client.post(
        "/graphql",
        data={"query": VALIDATION_RUN, "variables": variables},
        content_type="application/json",
    )
    pprint(resp.json())

    if allowed:
        node = resp.json()["data"]["validationRun"]
        assert node["id"] == to_global_id(
            "ValidationRunNode", validation_run.id
        )
        assert "inputHash" in node
        assert "success" in node
        assert "progress" in node
        assert "dataReview" in node
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_query_all_validation_runs(
    db, clients, data_review, user_group, allowed
):
    client = clients.get(user_group)
    if user_group:
        user = User.objects.filter(groups__name=user_group).first()
        Membership(collaborator=user, study=data_review.study).save()

    # Create some validation runs for each file
    n = 2
    for i in range(n):
        ValidationRunFactory(data_review=data_review)

    resp = client.post(
        "/graphql",
        data={"query": ALL_VALIDATION_RUNS},
        content_type="application/json",
    )

    if allowed:
        edges = resp.json()["data"]["allValidationRuns"]["edges"]
        assert len(edges) == n
        for edge in edges:
            assert "id" in edge["node"]
            assert "inputHash" in edge["node"]
            assert "success" in edge["node"]
            assert "progress" in edge["node"]
            assert "dataReview" in edge["node"]
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
