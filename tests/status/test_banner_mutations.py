import pytest
import datetime
from graphql_relay import to_global_id

from creator.status.banners.factories import BannerFactory

CREATE_BANNER = """
mutation ($input: BannerInput!) {
    createBanner(input: $input) {
        banner {
            id
            message
            severity
            enabled
            startDate
            endDate
            url
            urlLabel
        }
    }
}
"""

UPDATE_BANNER = """
mutation ($id: ID!, $input: BannerInput!) {
    updateBanner(id: $id, input: $input) {
        banner {
            id
            message
            severity
            enabled
            startDate
            endDate
            url
            urlLabel
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
def test_create_banner(db, clients, user_group, allowed):
    """
    Test the create mutation.
    """
    client = clients.get(user_group)
    data = {
        "query": CREATE_BANNER,
        "variables": {
            "input": {
                "message": "This is a notification",
                "severity": "INFO",
                "enabled": True,
                "url": "https://www.example.com",
                "urlLabel": "View more info here",
                "startDate": datetime.datetime.now().isoformat(),
                "endDate": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat()
            }
        }
    }
    resp = client.post(
        "/graphql", data=data, content_type="application/json",
    )
    if allowed:
        created_banner = resp.json()["data"]["createBanner"]["banner"]
        assert created_banner is not None
        for k, v in data["variables"]["input"].items():
            assert v == created_banner[k]
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
def test_update_banner(db, clients, user_group, allowed):
    """
    Test the update mutation.
    """
    client = clients.get(user_group)

    banner = BannerFactory()
    data = {
        "query": UPDATE_BANNER,
        "variables": {
            "id": to_global_id("BannerNode", banner.id),
            "input": {
                "message": "This is a notification",
                "severity": "INFO",
                "enabled": not banner.enabled,
                "url": "https://www.example.com",
                "urlLabel": "View more info here",
                "startDate": datetime.datetime.now().isoformat(),
                "endDate": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat()
            }
        }
    }
    resp = client.post(
        "/graphql",
        data=data,
        content_type="application/json",
    )

    if allowed:
        updated_banner = resp.json()["data"]["updateBanner"]["banner"]
        assert updated_banner is not None
        for k, v in data["variables"]["input"].items():
            assert v == updated_banner[k]
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
