import jwt
import pytest
import mock
from creator.studies.factories import StudyFactory


def test_corrupt_jwt(db, clients):
    """
    Test that a poorly formatted token fails validation and don't return any
    studies
    """
    client = clients.get(None)
    s = StudyFactory(name="test", kf_id="SD_ME0WME0W")
    s.save()
    q = "{ allStudies { edges { node { name } } } }"
    resp = client.post(
        "/graphql",
        data={"query": q},
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer undefined",
    )
    assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_invalid_jwt(db, client, token):
    """
    Test that an improperly signed token fails validation
    """
    s = StudyFactory(name="test", kf_id="SD_ME0WME0W")
    s.save()
    decoded = jwt.decode(token(), verify=False)
    with open("tests/keys/other_private_key.pem") as f:
        key = f.read()
    encoded = jwt.encode(decoded, key, algorithm="RS256").decode("utf-8")
    q = "{ allStudies { edges { node { name } } } }"

    resp = client.post(
        "/graphql",
        data={"query": q},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {str(encoded)}",
    )
    assert resp.json()["errors"][0]["message"] == "Not allowed"
