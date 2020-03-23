import pytest
from django.contrib.auth import get_user_model
from creator.files.models import File
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory

User = get_user_model()

update_query = """
mutation (
    $kfId:String!,
    $description: String!,
    $name: String!,
    $fileType: FileFileType!
    $tags: [String]
) {
    updateFile(
        kfId: $kfId,
        name: $name,
        description:$description,
        fileType: $fileType
        tags: $tags
    ) {
        file { id kfId description name fileType tags }
    }
}
"""


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


def test_unauthed_file_mutation_query(db, clients, versions):
    """
    File mutations are not allowed without authentication
    """
    client = clients.get(None)
    study, file, version = versions

    query = update_query
    variables = {
        "kfId": file.kf_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["updateFile"] is None
    expected_error = "Not allowed"
    assert resp.json()["errors"][0]["message"] == expected_error


def test_my_file_mutation_query(db, clients, versions):
    """
    File mutations are allowed on the files under the studies that
    the user belongs to
    """
    client = clients.get("Investigators")
    study, file, version = versions
    User.objects.filter(groups__name="Investigators").first().studies.add(
        study
    )

    query = update_query
    variables = {
        "kfId": file.kf_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
        "tags": ["tag1", "tag2"],
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    resp_file = resp.json()["data"]["updateFile"]["file"]
    assert resp_file["name"] == "New name"
    assert resp_file["description"] == "New description"
    assert resp_file["tags"] == ["tag1", "tag2"]


def test_not_my_file_mutation_query(db, clients, versions):
    """
    File mutations are not allowed on the files under the studies that
    the user does not belong to
    """
    client = clients.get("Investigators")
    study, file, version = versions

    query = update_query
    variables = {
        "kfId": file.kf_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["updateFile"] is None
    expected_error = "Not allowed"
    assert resp.json()["errors"][0]["message"] == expected_error


def test_admin_file_mutation_query(db, clients, versions):
    """
    File mutations are allowed on any files for admin user
    """
    client = clients.get("Administrators")
    study, file, version = versions

    query = update_query
    variables = {
        "kfId": file.kf_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
        "tags": ["tag1", "tag2"],
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    resp_file = resp.json()["data"]["updateFile"]["file"]
    assert resp_file["name"] == "New name"
    assert resp_file["description"] == "New description"
    assert resp_file["tags"] == ["tag1", "tag2"]


def test_no_tags(db, clients, versions):
    """
    Files should be able to be updated with empty tagset.
    """
    client = clients.get("Investigators")
    study, file, version = versions
    User.objects.filter(groups__name="Investigators").first().studies.add(
        study
    )

    query = update_query
    variables = {
        "kfId": file.kf_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
        "tags": ["tag1", "tag2"],
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    resp_file = resp.json()["data"]["updateFile"]["file"]
    assert resp_file["tags"] == ["tag1", "tag2"]
    assert len(File.objects.first().tags) == 2

    # Update file with empty tagset
    variables = {
        "kfId": file.kf_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
        "tags": [],
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    resp_file = resp.json()["data"]["updateFile"]["file"]
    assert resp_file["tags"] == []
    assert len(File.objects.first().tags) == 0
