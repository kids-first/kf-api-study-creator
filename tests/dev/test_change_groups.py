import pytest
from django.core import management
from django.contrib.auth import get_user_model

User = get_user_model()


def test_change_groups(db, client, dev_endpoints):
    """
    Test that the dev endpoint is not mounted unless it is enabled
    """
    management.call_command("setup_test_user")
    user = User.objects.get(username="testuser")
    assert user.groups.first().name == "Administrators"

    resp = client.post(
        "/__dev/change-groups/?groups=Administrators,Developers"
    )
    assert resp.json()["status"] == "done"

    assert user.groups.count() == 2
    assert {g.name for g in user.groups.all()} == {
        "Administrators",
        "Developers",
    }


def test_no_groups(db, client, dev_endpoints):
    """
    Test that the dev endpoint is not mounted unless it is enabled
    """
    management.call_command("setup_test_user")
    user = User.objects.get(username="testuser")
    assert user.groups.first().name == "Administrators"

    resp = client.post("/__dev/change-groups/")
    assert resp.json()["status"] == "done"

    assert user.groups.count() == 0


def test_no_user(db, client, dev_endpoints):
    """
    Test response when user is not found
    """
    resp = client.post("/__dev/change-groups/")
    assert resp.json()["status"] == "fail"


def test_missing_group(db, client, dev_endpoints):
    """
    Test that no action is taken if one or more of the groups are not found
    """
    management.call_command("setup_test_user")
    user = User.objects.get(username="testuser")

    resp = client.post("/__dev/change-groups/?groups=Developers,Blah")
    assert resp.json()["status"] == "fail"
    assert "One or more of the groups" in resp.json()["message"]

    assert user.groups.count() == 1
    assert {g.name for g in user.groups.all()} == {"Administrators"}


def test_post_only(db, client, dev_endpoints):
    """
    Test that endpoints only work for post
    """

    resp = client.get("/__dev/change-groups/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "fail"
    assert resp.json()["message"] == "Only POST is supported"
