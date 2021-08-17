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
def test_link_bucket(db, user_group, allowed, clients):
    """
    Test that only admins may link a bucket to a study
    """
    study = StudyFactory(buckets=None, files=0)
    bucket = BucketFactory()

    client = clients.get(user_group)

    resp = client.post(
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

    if allowed:
        assert (
            len(resp.json()["data"]["linkBucket"]["study"]["buckets"]["edges"])
            == 1
        )
        assert Bucket.objects.first().study == study
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert Bucket.objects.first().study is None


def test_double_link_bucket(db, clients):
    """
    Test that linking a bucket again does not remove or change a link
    """
    client = clients.get("Administrators")

    study = StudyFactory(buckets=None, files=0)
    bucket = BucketFactory()

    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "bucket": to_global_id("BucketNode", bucket.name),
    }

    assert Bucket.objects.first().study is None

    # Link once
    resp = client.post(
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
    resp = client.post(
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
def test_bucket_does_not_exist(db, clients, query):
    """
    Test that a bucket cannot be (un)linked if it doesn't exist
    """
    client = clients.get("Administrators")
    study = StudyFactory(buckets=None)

    variables = {
        "study": to_global_id("StudyNode", study.kf_id),
        "bucket": "blah",
    }

    resp = client.post(
        "/graphql",
        data={"query": query, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Bucket does not exist" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize("query", [LINK_BUCKET, UNLINK_BUCKET])
def test_study_does_not_exist(db, clients, query):
    """
    Test that a bucket cannot be (un)linked if it the study doesn't exist
    """
    client = clients.get("Administrators")
    bucket = BucketFactory()

    variables = {
        "study": "blah",
        "bucket": to_global_id("BucketNode", bucket.name),
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
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_unlink_bucket(db, user_group, allowed, clients):
    """
    Test that only admins may unlink a bucket
    """
    study = StudyFactory(buckets=None, files=0)
    bucket = BucketFactory()
    bucket.study = study
    bucket.save()

    assert Bucket.objects.first().study == study

    client = clients.get(user_group)

    resp = client.post(
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

    if allowed:
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
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert Bucket.objects.first().study == study


def test_unlink_bucket_no_link(db, clients):
    """
    Test that unlinking a bucket that isn't linked doesn't change anything
    """
    client = clients.get("Administrators")
    study = StudyFactory(buckets=None, files=0)
    bucket = BucketFactory()

    assert Bucket.objects.first().study is None

    resp = client.post(
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
