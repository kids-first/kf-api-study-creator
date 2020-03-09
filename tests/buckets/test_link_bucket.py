import pytest
from graphql_relay import to_global_id

from creator.studies.models import Study
from creator.studies.factories import StudyFactory

from creator.buckets.models import Bucket
from creator.buckets.factories import BucketFactory


LINK_BUCKET = """
mutation ($study: ID!, $bucket: ID!) {
    linkBucket(study: $study, bucket: $bucket) {
        study {
            id
            kfId
            buckets { edges { node { id name} } }
        }
    }
}
"""

UNLINK_BUCKET = """
mutation ($study: ID!, $bucket: ID!) {
    unlinkBucket(study: $study, bucket: $bucket) {
        study {
            id
            kfId
            buckets { edges { node { id name } } }
        }
        bucket {
            id
            name
            study { id kfId }
        }
    }
}
"""


@pytest.mark.parametrize(
    "user_type,expected",
    [("admin", True), ("service", True), ("user", False), (None, False)],
)
def test_link_bucket(
    db, user_type, expected, admin_client, service_client, user_client, client
):
    """
    Test that only admins may link a bucket to a study
    """
    study = StudyFactory()
    bucket = BucketFactory()

    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]

    resp = api_client.post(
        "/graphql",
        data={
            "query": LINK_BUCKET,
            "variables": {
                "study": to_global_id("StudyNode", study.kf_id),
                "bucket": to_global_id("BucketNode", bucket.name),
            },
        },
        content_type="application/json",
    )

    if expected:
        assert (
            len(
                resp.json()["data"]["linkBucket"]["study"]["buckets"][
                    "edges"
                ]
            )
            == 1
        )
        assert Bucket.objects.first().study == study
    else:
        assert (
            resp.json()["errors"][0]["message"]
            == "Not authenticated to link a bucket."
        )
        assert Bucket.objects.first().study is None


def test_double_link_bucket(db, admin_client):
    """
    Test that linking a bucket again does not remove or change a link
    """
    study = StudyFactory()
    bucket = BucketFactory()

    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "bucket": to_global_id("BucketNode", bucket.name),
    }

    assert Bucket.objects.first().study is None

    # Link once
    resp = admin_client.post(
        "/graphql",
        data={"query": LINK_BUCKET, "variables": variables},
        content_type="application/json",
    )
    assert (
        len(resp.json()["data"]["linkBucket"]["study"]["buckets"]["edges"])
        == 1
    )
    assert Bucket.objects.first().study == study

    # Link again
    resp = admin_client.post(
        "/graphql",
        data={"query": LINK_BUCKET, "variables": variables},
        content_type="application/json",
    )
    assert (
        len(resp.json()["data"]["linkBucket"]["study"]["buckets"]["edges"])
        == 1
    )
    assert Bucket.objects.first().study == study


@pytest.mark.parametrize("query", [LINK_BUCKET, UNLINK_BUCKET])
def test_bucket_does_not_exist(db, admin_client, query):
    """
    Test that a bucket cannot be (un)linked if it doesn't exist
    """
    study = StudyFactory()

    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "bucket": "blah",
    }

    resp = admin_client.post(
        "/graphql",
        data={"query": query, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Bucket does not exist" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize("query", [LINK_BUCKET, UNLINK_BUCKET])
def test_study_does_not_exist(db, admin_client, query):
    """
    Test that a bucket cannot be (un)linked if it the study doesn't exist
    """
    bucket = BucketFactory()

    variables = {
        "study": "blah",
        "bucket": to_global_id("BucketNode", bucket.name),
    }

    resp = admin_client.post(
        "/graphql",
        data={"query": query, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Study does not exist" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "user_type,expected",
    [("admin", True), ("service", True), ("user", False), (None, False)],
)
def test_unlink_bucket(
    db, user_type, expected, admin_client, service_client, user_client, client
):
    """
    Test that only admins may unlink a bucket
    """
    study = StudyFactory()
    bucket = BucketFactory()
    bucket.study = study
    bucket.save()

    assert Bucket.objects.first().study == study

    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]

    resp = api_client.post(
        "/graphql",
        data={
            "query": UNLINK_BUCKET,
            "variables": {
                "study": to_global_id("StudyNode", study.kf_id),
                "bucket": to_global_id("BucketNode", bucket.name),
            },
        },
        content_type="application/json",
    )

    if expected:
        assert (
            len(
                resp.json()["data"]["unlinkBucket"]["study"]["buckets"][
                    "edges"
                ]
            )
            == 0
        )
        assert resp.json()["data"]["unlinkBucket"]["bucket"]["study"] is None
        assert Bucket.objects.first().study is None
    else:
        assert (
            resp.json()["errors"][0]["message"]
            == "Not authenticated to unlink a bucket."
        )
        assert Bucket.objects.first().study == study


def test_unlink_bucket_no_link(db, admin_client):
    """
    Test that unlinking a bucket that isn't linked doesn't change anything
    """
    study = StudyFactory()
    bucket = BucketFactory()

    assert Bucket.objects.first().study is None

    resp = admin_client.post(
        "/graphql",
        data={
            "query": UNLINK_BUCKET,
            "variables": {
                "study": to_global_id("StudyNode", study.kf_id),
                "bucket": to_global_id("BucketNode", bucket.name),
            },
        },
        content_type="application/json",
    )

    assert (
        len(resp.json()["data"]["unlinkBucket"]["study"]["buckets"]["edges"])
        == 0
    )
    assert resp.json()["data"]["unlinkBucket"]["bucket"]["study"] is None
    assert Bucket.objects.first().study is None
