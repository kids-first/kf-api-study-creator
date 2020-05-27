import pytest
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model
from creator.referral_tokens.factories import ReferralTokenFactory

User = get_user_model()

REFERRALTOKEN = """
query ($id: ID!) {
  referralToken(id: $id) {
    id
    email
  }
}
"""

ALL_REFERRALTOKENS = """
query {
    allReferralTokens {
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
def test_query_referral_token(db, clients, user_group, allowed):
    client = clients.get(user_group)

    referral_token = ReferralTokenFactory()
    variables = {"id": to_global_id("ReferralTokenNode", referral_token.uuid)}
    resp = client.post(
        "/graphql",
        data={"query": REFERRALTOKEN, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["referralToken"]["email"]
            == referral_token.email
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group,allowed,number",
    [
        ("Administrators", True, 2),
        ("Services", False, 0),
        ("Developers", False, 0),
        ("Investigators", False, 0),
        ("Bioinformatics", False, 0),
        (None, False, 0),
    ],
)
def test_query_all(db, clients, user_group, allowed, number):
    client = clients.get(user_group)
    if user_group:
        user = User.objects.get(groups__name=user_group)
        referral_tokens = ReferralTokenFactory.create_batch(2)

    resp = client.post(
        "/graphql",
        data={"query": ALL_REFERRALTOKENS},
        content_type="application/json",
    )

    if allowed:
        assert len(resp.json()["data"]["allReferralTokens"]["edges"]) == number
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
