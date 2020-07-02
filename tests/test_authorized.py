import pytest
from django.contrib.auth import get_user_model
from creator.studies.models import Membership
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory

User = get_user_model()


@pytest.fixture
def versions(db, clients, mocker):
    client = clients.get("Administrators")
    study = StudyFactory()
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")
    version.key = open(f"tests/data/manifest.txt")

    mock_resp = mocker.patch("creator.files.views._resolve_version")
    mock_resp.return_value = (file, version)

    return study, file, version


@pytest.mark.parametrize("resource", ["study", "file", "version"])
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
def test_get_resource_by_id(
    db, clients, versions, resource, user_group, allowed
):
    """
    Test that resource may be retrieved by (relay) id
    - Should return resource if admin
    - Should return resource if user who is part of study
    - Should return None if user who is not part of study
    - Should return None if not an authenticated user
    """
    # Select client based on user type
    admin_client = clients.get("Administrators")
    client = clients.get(user_group)
    study, file, version = versions
    user = User.objects.filter(groups__name=user_group).first()
    Membership(collaborator=user, study=study).save()

    # Get the id of the resource we're testing for
    kf_id = {
        "study": study.kf_id,
        "file": file.kf_id,
        "version": version.kf_id,
    }[resource]

    # Get a node's relay id using admin client
    query = f'{{{resource}ByKfId(kfId: "{kf_id}") {{ id }} }}'
    resp = admin_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert "id" in resp.json()["data"][f"{resource}ByKfId"]
    node_id = resp.json()["data"][f"{resource}ByKfId"]["id"]

    # Now try to get node by the relay id
    query = f'{{{resource}(id: "{node_id}") {{ id }} }}'
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )

    # Should get back the node with id if expected, None if not
    if allowed:
        assert resp.json()["data"][resource]["id"] == node_id
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize("resource", ["study", "file", "version"])
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
def test_get_resource_by_kf_id(
    db, clients, versions, resource, user_group, allowed
):
    """
    Test that resource may be retrieved by kfId
    - Will return resource if admin
    - Should return resource if user who is parto of study
    - Should return None if user who is not part of study
    - Should return None if not an authenticated user
    """
    # Select client based on user type
    client = clients.get(user_group)
    study, file, version = versions
    user = User.objects.filter(groups__name=user_group).first()
    Membership(collaborator=user, study=study).save()

    # Get the id of the resource we're testing for
    kf_id = {
        "study": study.kf_id,
        "file": file.kf_id,
        "version": version.kf_id,
    }[resource]

    # Test that a study may be retreived by kf_id
    query = f'{{{resource}ByKfId(kfId: "{kf_id}") {{ id kfId }} }}'
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )

    assert f"{resource}ByKfId" in resp.json()["data"]
    # Will return size if authenticated, None if not
    if allowed:
        assert "kfId" in resp.json()["data"][f"{resource}ByKfId"]
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
