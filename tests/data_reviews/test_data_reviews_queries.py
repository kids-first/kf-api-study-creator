import pytest
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model
from creator.studies.models import Membership
from creator.data_reviews.factories import DataReviewFactory
from creator.ingest_runs.factories import ValidationResultsetFactory
from creator.studies.models import Study

User = get_user_model()

DATA_REVIEW = """
query ($id: ID!) {
    dataReview(id: $id) {
        id
        kfId
        createdAt
        name
        description
        state
        validationResultset {
            id failed passed didNotRun downloadReportUrl downloadResultsUrl
        }
        study { id kfId }
        versions { edges { node { id kfId } } }
    }
}
"""

ALL_DATA_REVIEWS = """
query {
    allDataReviews {
        edges {
            node {
                id
                kfId
                createdAt
                name
                description
                state
                validationResultset {
                    id failed passed didNotRun downloadReportUrl downloadResultsUrl # noqa
                }
                study { id kfId }
                versions { edges { node { id kfId } } }
            }
        }
    }
}
"""

ALL_DATA_REVIEWS_BY_STUDY = """
query($studyKfId: String) {
    allDataReviews(studyKfId: $studyKfId) {
        edges {
            node {
                id
                kfId
                createdAt
                name
                description
                state
                validationResultset { id failed passed didNotRun }
                study { id kfId }
                versions { edges { node { id kfId } } }
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
def test_query_data_review(
    db, clients, prep_file, data_review, user_group, allowed
):
    client = clients.get(user_group)

    if user_group:
        user = User.objects.filter(groups__name=user_group).first()
        Membership(collaborator=user, study=data_review.study).save()

    variables = {"id": to_global_id("DataReviewNode", data_review.pk)}
    resp = client.post(
        "/graphql",
        data={"query": DATA_REVIEW, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        dr = resp.json()["data"]["dataReview"]
        # Check data review basic attrs
        assert dr["id"] == to_global_id(
            "DataReviewNode", data_review.pk
        )
        for attr in ["name", "description", "state"]:
            assert getattr(data_review, attr) == dr[attr]

        # Check data review validation resultset
        vrs = dr["validationResultset"]
        for attr in ["failed", "passed", "didNotRun"]:
            assert vrs[attr] is not None
        assert vrs["downloadReportUrl"] == (
            f"https://testserver/download/data_review/{data_review.kf_id}"
            "/validation/report"
        )
        assert vrs["downloadResultsUrl"] == (
            f"https://testserver/download/data_review/{data_review.kf_id}"
            "/validation/results"
        )
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
def test_query_all_data_reviews(db, clients, prep_file, user_group, allowed):
    client = clients.get(user_group)

    # Create a study with some files
    for i in range(2):
        prep_file(authed=True)
    # Create Data Review
    drs = DataReviewFactory.create_batch(5)

    if user_group:
        user = User.objects.filter(groups__name=user_group).first()
        Membership(collaborator=user, study=drs[0].study).save()

    resp = client.post(
        "/graphql",
        data={"query": ALL_DATA_REVIEWS},
        content_type="application/json",
    )

    if allowed:
        assert len(resp.json()["data"]["allDataReviews"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
    ],
)
def test_query_filter_data_reviews(
    db, clients, prep_file, user_group, allowed
):
    client = clients.get(user_group)

    # Create a study with some files
    for i in range(2):
        prep_file(authed=True)

    # Create Data Review
    for s in Study.objects.all():
        dr = DataReviewFactory(study=s)

    resp = client.post(
        "/graphql",
        data={
            "query": ALL_DATA_REVIEWS,
            "variables": {"studyKfId": dr.study.pk},
        },
        content_type="application/json",
    )

    drs = resp.json()["data"]["allDataReviews"]["edges"]
    assert len(drs) == 1
    assert drs[0]["node"]["study"]["kfId"] == dr.study.pk
