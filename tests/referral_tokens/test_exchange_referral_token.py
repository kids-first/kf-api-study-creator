import pytest
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from creator.events.models import Event
from creator.studies.models import Study, Membership
from creator.referral_tokens.models import ReferralToken
from creator.studies.factories import StudyFactory
from creator.referral_tokens.factories import ReferralTokenFactory


User = get_user_model()

EXCHANGE_REFERRALTOKEN = """
mutation ($token: ID!) {
  exchangeReferralToken(token: $token) {
    referralToken {
      uuid
      claimed
      isValid
      organization {
          id
      }
    }
    user {
      email
      organizations {
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
      groups {
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

CREATE_REFERRALTOKEN = """
mutation newReferralToken($input: ReferralTokenInput!) {
  createReferralToken(input: $input) {
    referralToken {
      uuid
      claimed
      isValid
      organization {
          id
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
def test_exchange_referral_token(db, clients, user_group, allowed):
    """
    All login user can exchange referral token
    """
    client = clients.get(user_group)
    kwargs = {}

    if allowed:
        user = User.objects.get(username=f"{user_group} User")
        kwargs["email"] = user.email
    referral_token = ReferralTokenFactory(**kwargs)
    num_studies = referral_token.studies.count()
    assert ReferralToken.objects.first().claimed is False

    resp = client.post(
        "/graphql",
        data={
            "query": EXCHANGE_REFERRALTOKEN,
            "variables": {
                "token": to_global_id("ReferralTokenNode", referral_token.uuid)
            },
        },
        content_type="application/json",
    )

    if allowed:
        resp_body = resp.json()["data"]["exchangeReferralToken"]

        assert resp_body["referralToken"]["isValid"] is False
        assert ReferralToken.objects.first().claimed is True

        # Check Event
        rt_events = Event.objects.filter(event_type="RT_CLA").all()
        assert len(rt_events) == 1
        ev = rt_events.first()
        assert f"claimed token for {num_studies} studies." in ev.description
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_exchange_referral_token_no_multiple_claim(db, clients):
    """
    User cannot exchange referral token when it is not valid
    """
    client = clients.get("Administrators")
    user = User.objects.get(username="Administrators User")
    referral_token = ReferralTokenFactory(email=user.email)
    resp_claim = client.post(
        "/graphql",
        data={
            "query": EXCHANGE_REFERRALTOKEN,
            "variables": {
                "token": to_global_id("ReferralTokenNode", referral_token.uuid)
            },
        },
        content_type="application/json",
    )
    resp_invalid = client.post(
        "/graphql",
        data={
            "query": EXCHANGE_REFERRALTOKEN,
            "variables": {
                "token": to_global_id("ReferralTokenNode", referral_token.uuid)
            },
        },
        content_type="application/json",
    )
    assert (
        resp_invalid.json()["errors"][0]["message"]
        == "Referral token is not valid."
    )


def test_exchange_referral_token_not_exist(db, clients):
    """
    User cannot exchange referral token when it does not exist
    """
    client = clients.get("Administrators")
    random_token = (
        "UmVmZXJyYWxUb2tlbk5vZGU6ODBjZWY2ZjItNjA5OC00MjYyLTg3MDY"
        "tMTAzNjVlM2ZhOTRh"
    )
    resp = client.post(
        "/graphql",
        data={
            "query": EXCHANGE_REFERRALTOKEN,
            "variables": {"token": random_token},
        },
        content_type="application/json",
    )
    assert (
        resp.json()["errors"][0]["message"] == "Referral token does not exist."
    )


def test_exchange_referral_token_expired(db, clients, settings):
    """
    User cannot exchange referral token when it is expired
    """
    client = clients.get("Administrators")
    user = User.objects.filter(groups__name="Administrators").first()
    # Reset the referral token expiring days to have an expired token
    settings.REFERRAL_TOKEN_EXPIRATION_DAYS = -1

    study = StudyFactory(kf_id="SD_00000000")
    study.organization.members.add(user)
    study_id = to_global_id("StudyNode", "SD_00000000")
    organization_id = to_global_id("OrganizationNode", study.organization.id)

    group = Group.objects.first()
    group_id = to_global_id("GroupNode", group.id)

    email = "test@email.com"
    variables = {
        "input": {
            "email": email,
            "studies": [study_id],
            "groups": [group_id],
            "organization": organization_id,
        }
    }

    resp_create = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_REFERRALTOKEN, "variables": variables},
    )
    resp_create_body = resp_create.json()["data"]["createReferralToken"]
    assert resp_create_body["referralToken"]["isValid"] is False
    assert ReferralToken.objects.count() == 1
    referral_token = ReferralToken.objects.first()

    resp_exchange = client.post(
        "/graphql",
        data={
            "query": EXCHANGE_REFERRALTOKEN,
            "variables": {
                "token": to_global_id("ReferralTokenNode", referral_token.uuid)
            },
        },
        content_type="application/json",
    )
    assert (
        resp_exchange.json()["errors"][0]["message"]
        == "Referral token is not valid."
    )


def test_exchange_referral_token_study_group_org(db, clients):
    """
    Studies, groups, and organization are correctly added to user on exchanging
    referral token
    """
    client = clients.get("Administrators")
    user = User.objects.filter(groups__name="Administrators").first()

    study = StudyFactory()
    study.organization.members.add(user)
    study_id = to_global_id("StudyNode", study.kf_id)
    organization_id = to_global_id("OrganizationNode", study.organization.id)

    group = Group.objects.first()
    group_id = to_global_id("GroupNode", group.id)

    invited_user = User.objects.get(username="Investigators User")
    variables = {
        "input": {
            "email": invited_user.email,
            "studies": [study_id],
            "groups": [group_id],
            "organization": organization_id,
        }
    }

    resp_create = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_REFERRALTOKEN, "variables": variables},
    )

    assert ReferralToken.objects.count() == 1
    assert Study.objects.first().collaborators.count() == 0

    referral_token = ReferralToken.objects.first()
    # The client above should be the admin inviting a new user to the study
    # creator. The client below should be this new user signing up and should
    # not be an admin anymore.
    client = clients.get("Investigators")
    resp_exchange = client.post(
        "/graphql",
        data={
            "query": EXCHANGE_REFERRALTOKEN,
            "variables": {
                "token": to_global_id("ReferralTokenNode", referral_token.uuid)
            },
        },
        content_type="application/json",
    )
    resp_body = resp_exchange.json()["data"]["exchangeReferralToken"]["user"]
    groups = [group["node"]["id"] for group in resp_body["groups"]["edges"]]
    assert group_id in groups
    assert resp_body["studies"]["edges"][0]["node"]["id"] == study_id
    assert (
        resp_body["organizations"]["edges"][0]["node"]["id"] == organization_id
    )
    assert Study.objects.first().collaborators.count() == 1


def test_exchange_referral_token_no_overwrite(db, clients):
    """
    Test that existing studies and groups are not overwritten by exchange
    """
    client = clients.get("Administrators")
    user = User.objects.filter(groups__name="Administrators").first()
    # Add user to one pre-existing study
    Membership(collaborator=user, study=StudyFactory()).save()

    # Generate new study and group to invite user to
    study = StudyFactory()
    study.organization.members.add(user)
    study_id = to_global_id("StudyNode", study.kf_id)
    organization_id = to_global_id("OrganizationNode", study.organization.id)

    group = Group.objects.first()
    group_id = to_global_id("GroupNode", group.id)

    invited_user = User.objects.get(username="Administrators User")
    variables = {
        "input": {
            "email": invited_user.email,
            "studies": [study_id],
            "groups": [group_id],
            "organization": organization_id,
        }
    }

    resp_create = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_REFERRALTOKEN, "variables": variables},
    )

    referral_token = ReferralToken.objects.first()
    resp_exchange = client.post(
        "/graphql",
        data={
            "query": EXCHANGE_REFERRALTOKEN,
            "variables": {
                "token": to_global_id("ReferralTokenNode", referral_token.uuid)
            },
        },
        content_type="application/json",
    )
    resp_body = resp_exchange.json()["data"]["exchangeReferralToken"]["user"]
    assert len(resp_body["studies"]["edges"]) == 2
    assert user.studies.count() == 2


def test_exchange_referral_token_no_dupes(db, clients):
    """
    Test that inviting a user to a study they already belong to does not double
    count relationships
    """
    client = clients.get("Administrators")
    user = User.objects.filter(groups__name="Administrators").first()

    study = StudyFactory()
    study.organization.members.add(user)
    # Add user to new study
    Membership(collaborator=user, study=study).save()

    group = Group.objects.first()

    # Make token containing study the user already belongs to
    invited_user = User.objects.get(username="Administrators User")
    referral_token = ReferralToken(
        email=invited_user.email, organization=study.organization
    )
    referral_token.save()
    referral_token.studies.set([study])
    referral_token.groups.set([group])

    resp_exchange = client.post(
        "/graphql",
        data={
            "query": EXCHANGE_REFERRALTOKEN,
            "variables": {
                "token": to_global_id("ReferralTokenNode", referral_token.uuid)
            },
        },
        content_type="application/json",
    )

    resp_body = resp_exchange.json()["data"]["exchangeReferralToken"]["user"]
    assert len(resp_body["studies"]["edges"]) == 1
    assert user.studies.count() == 1


def test_exchange_referral_token_email(db, clients):
    """
    Test that an error is thrown when the invited user's email and the
    ReferralToken's email do not match
    """

    client = clients.get("Investigators")
    referral_token = ReferralTokenFactory()
    invited_user = User.objects.get(username="Investigators User")
    assert referral_token.email != invited_user.email

    resp = client.post(
        "/graphql",
        data={
            "query": EXCHANGE_REFERRALTOKEN,
            "variables": {
                "token": to_global_id("ReferralTokenNode", referral_token.uuid)
            },
        },
        content_type="application/json",
    )

    assert "cannot use this referral" in resp.json()["errors"][0]["message"]
