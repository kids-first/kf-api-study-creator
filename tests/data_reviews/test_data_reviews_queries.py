import pytest
from graphql_relay import to_global_id
from creator.data_reviews.factories import DataReviewFactory

DATA_REVIEW = """
query ($id: ID!) {
    dataReview(id: $id) {
        id
    }
}
"""

ALL_DATA_REVIEWS = """
query {
    allDataReviews {
        edges { node { id } }
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
def test_query_data_review(db, clients, user_group, allowed):
    client = clients.get(user_group)

    data_review = DataReviewFactory()

    variables = {"id": to_global_id("DataReviewNode", data_review.id)}

    resp = client.post(
        "/graphql",
        data={"query": DATA_REVIEW, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["dataReview"]["id"] ==
            to_global_id("DataReviewNode", data_review.id)
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


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
def test_query_all_data_reviews(db, clients, user_group, allowed):
    client = clients.get(user_group)

    data_review = DataReviewFactory.create_batch(5)

    resp = client.post(
        "/graphql",
        data={"query": ALL_DATA_REVIEWS}, content_type="application/json"
    )

    if allowed:
        assert len(resp.json()["data"]["allDataReviews"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
