import pytest
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model
from creator.files.models import Version
from creator.organizations.factories import OrganizationFactory
from creator.studies.models import Membership
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory, VersionFactory

User = get_user_model()

update_query = """
mutation (
    $kfId:String!,
    $state: VersionState!,
    $description: String!,
    $file: ID,
) {
    updateVersion(
        kfId: $kfId,
        description: $description
        state: $state
        file: $file
    ) {
        version {
            id
            kfId
            state
            description
            size
            rootFile { kfId }
        }
    }
}
"""


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", False),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_update_version_meta_auth(db, clients, versions, user_group, allowed):
    """
    Test that versions description may be updated only by admin or owners.
    """
    client = clients.get(user_group)
    study, file, version = versions

    query = update_query
    variables = {
        "kfId": version.kf_id,
        "description": "New description",
        "state": version.state,
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    # The operation should be successful
    if allowed:
        assert resp.status_code == 200
        assert (
            resp.json()["data"]["updateVersion"]["version"]["description"]
            == "New description"
        )
        version = Version.objects.get(kf_id=version.kf_id)
        assert version.description == "New description"
    # Should not be successful
    else:
        assert resp.status_code == 200
        assert resp.json()["data"]["updateVersion"] is None
        expected_error = "Not allowed"
        assert resp.json()["errors"][0]["message"] == expected_error


def test_my_version_meta(db, clients, versions):
    """
    Version meta mutations are allowed on the files under the studies that
    the user belongs to
    """
    client = clients.get("Investigators")
    study, file, version = versions
    user = User.objects.filter(groups__name="Investigators").first()
    Membership(collaborator=user, study=study).save()

    query = update_query
    variables = {
        "kfId": version.kf_id,
        "description": "New description",
        "state": version.state,
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    # The operation should be successful
    assert resp.status_code == 200
    assert (
        resp.json()["data"]["updateVersion"]["version"]["description"]
        == "New description"
    )
    version = Version.objects.get(kf_id=version.kf_id)
    assert version.description == "New description"


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
def test_update_version_status_auth(db, clients, user_group, allowed):
    """
    Test that versions status may be updated only by admin.
    """
    client = clients.get(user_group)
    study = StudyFactory()
    file = FileFactory(study=study)
    version = VersionFactory(state="PEN", root_file=file)

    query = update_query
    variables = {
        "kfId": version.kf_id,
        "description": version.description,
        "state": "APP",
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    # The operation should be successful
    if allowed:
        assert resp.status_code == 200
        assert (
            resp.json()["data"]["updateVersion"]["version"]["state"] == "APP"
        )
        version = Version.objects.get(kf_id=version.kf_id)
        assert version.state == "APP"
    # Should not be successful
    else:
        assert resp.status_code == 200
        assert resp.json()["data"]["updateVersion"] is None
        expected_error = "Not allowed"
        assert resp.json()["errors"][0]["message"] == expected_error


@pytest.mark.parametrize(
    "state,expected",
    [
        ("PEN", True),
        ("APP", True),
        ("CHN", True),
        ("PRC", True),
        ("OTH", 'Variable "$state" got invalid value'),
        ("XXX", 'Variable "$state" got invalid value'),
        ("Approved", 'Variable "$state" got invalid value'),
        (None, 'required type "VersionState!" was not provided'),
    ],
)
def test_update_state(db, clients, versions, state, expected):
    """
    Test that only valid states may be set.

    :state: Value to pass as the state field
    :expected: True if expected to pass, substring of the error message if
        it's expected to fail
    """
    client = clients.get("Administrators")
    study, file, version = versions

    query = update_query
    variables = {"kfId": version.kf_id, "description": "Test", "state": state}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    # The state is valid
    if expected is True:
        assert resp.status_code == 200
        assert (
            resp.json()["data"]["updateVersion"]["version"]["state"] == state
        )
        version = Version.objects.get(kf_id=version.kf_id)
        assert version.state == state
    # State is not known
    else:
        assert resp.status_code == 400
        assert expected in resp.json()["errors"][0]["message"]
        version = Version.objects.get(kf_id=version.kf_id)


def test_update_version_file(db, permission_client):
    """
    Test that versions may be updated with a new root file
    """
    user, client = permission_client(["change_version_meta"])
    org = OrganizationFactory(id="854612d1-2329-4469-b4e5-e51b481ab1dc")
    study = StudyFactory(kf_id="SD_ME0WME0W", organization=org)
    file = FileFactory(study=study)
    version = VersionFactory(study=study)

    query = update_query
    variables = {
        "kfId": version.kf_id,
        "description": "New description",
        "state": version.state,
        "file": to_global_id("FileNode", file.kf_id),
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    assert resp.status_code == 200
    assert (
        resp.json()["data"]["updateVersion"]["version"]["rootFile"]["kfId"]
        == file.kf_id
    )
    version = Version.objects.get(kf_id=version.kf_id)
    assert version.root_file == file


def test_update_version_no_study(db, clients):
    """
    Test that a version may not be modified if the study cannot be resolved.
    """
    client = clients.get("Administrators")
    version = VersionFactory(study=None, root_file=None)

    query = update_query
    variables = {
        "kfId": version.kf_id,
        "description": "New description",
        "state": version.state,
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    assert resp.status_code == 200
    assert "errors" in resp.json()
    assert "must be part of a study" in resp.json()["errors"][0]["message"]
