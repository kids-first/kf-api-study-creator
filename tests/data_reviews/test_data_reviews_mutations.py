import pytest
from graphql_relay import to_global_id

from creator.data_reviews.models import DataReview
from creator.data_reviews.factories import DataReviewFactory


CREATE_DATA_REVIEW = """
mutation ($input: CreateDataReviewInput!) {
    createDataReview(input: $input) {
        dataReview {
            id
        }
    }
}
"""

UPDATE_DATA_REVIEW = """
mutation ($id: ID!, $input: UpdateDataReviewInput!) {
    updateDataReview(id: $id, input: $input) {
        dataReview {
            id
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
def test_create_data_review(db, clients, user_group, allowed):
    """
    Test the create mutation.
    """
    client = clients.get(user_group)

    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_DATA_REVIEW,
            "variables": {"input": {"name": "Test"}}
        },
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["createDataReview"][
                "dataReview"]
            is not None
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
def test_update_data_review(db, clients, user_group, allowed):
    """
    Test the update mutation.
    """
    client = clients.get(user_group)

    data_review = DataReviewFactory()

    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_DATA_REVIEW,
            "variables": {
                "id": to_global_id("DataReviewNode}}", data_review.id),
                "input": {"name": "test"},
            },
        },
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["updateDataReview"]["dataReview"]
            is not None
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
