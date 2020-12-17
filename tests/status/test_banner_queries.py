import pytest
from graphql_relay import to_global_id
from creator.status.banners.factories import BannerFactory

BANNER = """
query ($id: ID!) {
    banner(id: $id) {
        id
        message
        enabled
        severity
        startDate
        endDate
    }
}
"""

ALL_BANNERS = """
query {
   allBanners {
       edges {
         node {
           id
           message
           enabled
           severity
           startDate
           endDate
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
def test_query_banner(db, clients, user_group, allowed):
    client = clients.get(user_group)

    banner = BannerFactory()

    variables = {"id": to_global_id("BannerNode", banner.id)}

    resp = client.post(
        "/graphql",
        data={"query": BANNER, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["banner"]["id"] ==
            to_global_id("BannerNode", banner.id)
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
def test_query_all_banner(db, clients, user_group, allowed):
    client = clients.get(user_group)

    banner = BannerFactory.create_batch(5)

    resp = client.post(
        "/graphql",
        data={"query": ALL_BANNERS},
        content_type="application/json"
    )

    if allowed:
        assert len(resp.json()["data"]["allBanners"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
