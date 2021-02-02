import pytest
from datetime import timedelta
from graphql_relay import to_global_id
from creator.studies.models import Study
from django.contrib.auth.models import Group
from creator.referral_tokens.models import ReferralToken

CREATE_REFERRALTOKEN = """
mutation newReferralToken($input: ReferralTokenInput!) {
  createReferralToken(input: $input) {
    referralToken {
      uuid
      email
      claimed
      isValid
      groups {
        edges {
          node {
            id
          }
        }
      }
      studies {
        edges {
          node {
            id
          }
        }
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
        ("Developers", False),
        ("Investigators", False),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_create_referral_token_mutation(db, clients, user_group, allowed):
    """
    Test that correct users may create referral token
    """
    client = clients.get(user_group)

    study = Study(kf_id="SD_00000000")
    study.save()
    study_id = to_global_id("StudyNode", "SD_00000000")

    group = Group.objects.first()
    group_id = to_global_id("GroupNode", group.id)

    email = "test@email.com"
    variables = {
        "input": {"email": email, "studies": [study_id], "groups": [group_id]}
    }

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_REFERRALTOKEN, "variables": variables},
    )

    if allowed:
        resp_body = resp.json()["data"]["createReferralToken"]["referralToken"]
        assert resp_body["email"] == email
        assert resp_body["isValid"] is True
        assert resp_body["groups"]["edges"][0]["node"]["id"] == group_id
        assert resp_body["studies"]["edges"][0]["node"]["id"] == study_id
        assert ReferralToken.objects.count() == 1
        assert ReferralToken.objects.first().claimed is False
    else:
        assert ReferralToken.objects.count() == 0
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_create_referral_token_mutation_existing(db, clients):
    """
    Test that Admin cannot create a new referral token when there is an
    existing a valid referral token
    """
    client = clients.get("Administrators")

    study = Study(kf_id="SD_00000000")
    study.save()
    study_id = to_global_id("StudyNode", "SD_00000000")

    group = Group.objects.first()
    group_id = to_global_id("GroupNode", group.id)

    email = "test@email.com"
    variables = {
        "input": {"email": email, "studies": [study_id], "groups": [group_id]}
    }

    resp_create = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_REFERRALTOKEN, "variables": variables},
    )

    assert ReferralToken.objects.count() == 1

    resp_existing = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_REFERRALTOKEN, "variables": variables},
    )

    assert (
        resp_existing.json()["errors"][0]["message"]
        == "Invite already sent, awaiting user response"
    )
    assert ReferralToken.objects.count() == 1


def test_create_referral_token_mutation_expired(db, clients, settings):
    """
    Test that a refferal token may be 'resent' for the same user/email after
    the old token has expired.
    """
    client = clients.get("Administrators")

    study = Study(kf_id="SD_00000000")
    study.save()
    study_id = to_global_id("StudyNode", "SD_00000000")

    group = Group.objects.first()
    group_id = to_global_id("GroupNode", group.id)

    email = "test@email.com"
    variables = {
        "input": {"email": email, "studies": [study_id], "groups": [group_id]}
    }

    resp_create = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_REFERRALTOKEN, "variables": variables},
    )

    assert ReferralToken.objects.count() == 1

    # Now retrieve the token and roll back the created_at time so that it
    # will appear to have expired
    token = ReferralToken.objects.first()
    token.created_at = token.created_at - timedelta(
        days=(settings.REFERRAL_TOKEN_EXPIRATION_DAYS + 1)
    )
    token.save()

    # Should be able to create another, identical token now that it is expired
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_REFERRALTOKEN, "variables": variables},
    )

    assert "errors" not in resp.json()
    resp_body = resp.json()["data"]["createReferralToken"]["referralToken"]
    assert resp_body["email"] == email
    assert resp_body["isValid"] is True
    assert resp_body["groups"]["edges"][0]["node"]["id"] == group_id
    assert resp_body["studies"]["edges"][0]["node"]["id"] == study_id
    assert ReferralToken.objects.count() == 2
