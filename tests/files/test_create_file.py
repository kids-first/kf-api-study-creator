import pytest
from django.contrib.auth import get_user_model
from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.studies.models import Study, Membership
from creator.files.models import Version

from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory

User = get_user_model()


CREATE_FILE = """
    mutation (
        $version: ID!,
        $name: String!,
        $description: String!,
        $fileType: FileType!,
        $study: ID
        $tags: [String]
    ) {
        createFile(
          version: $version,
          name: $name,
          study: $study,
          description: $description,
          fileType: $fileType
          tags: $tags
        ) {
            file {
                id
                kfId
                name
                description
                fileType
                tags
                versions(orderBy: "-created_at") {
                    edges {
                        node {
                            id
                            analysis {
                                id
                            }
                        }
                    }
                }
            }
      }
    }
"""


def test_study_does_not_exist(db, clients):
    """
    Test that error is returned if the provided study is not found.
    """
    client = clients.get("Administrators")
    study = StudyFactory(kf_id="SD_ME0WME0W")
    file = FileFactory()
    version = file.versions.first()

    variables = {
        "version": to_global_id("VersionNode", version.kf_id),
        "name": "Test file",
        "study": to_global_id("StudyNode", "SD_00000000"),
        "description": "This is my test file",
        "fileType": "OTH",
        "tags": ["tag1", "tag2"],
    }

    data = {"query": CREATE_FILE, "variables": variables}
    resp = client.post("/graphql", content_type="application/json", data=data)

    assert "errors" in resp.json()
    assert "Study does not exist" in resp.json()["errors"][0]["message"]


def test_version_does_not_exist(db, clients):
    """
    Check that an error is returned if the provided version is not found.
    """
    client = clients.get("Administrators")

    variables = {
        "version": to_global_id("VersionNode", "FV_00000001"),
        "name": "Test file",
        "study": to_global_id("StudyNode", "SD_00000000"),
        "description": "This is my test file",
        "fileType": "OTH",
        "tags": ["tag1", "tag2"],
    }

    data = {"query": CREATE_FILE, "variables": variables}
    resp = client.post("/graphql", content_type="application/json", data=data)

    assert "errors" in resp.json()
    assert "Version does not exist" in resp.json()["errors"][0]["message"]


def test_version_or_study_required(db, clients):
    """
    Make sure either a study or version is required.
    """
    client = clients.get("Administrators")
    version = Version(size=123)
    version.save()

    variables = {
        "version": to_global_id("VersionNode", version.kf_id),
        "name": "Test file",
        "description": "This is my test file",
        "fileType": "OTH",
        "tags": ["tag1", "tag2"],
    }

    data = {"query": CREATE_FILE, "variables": variables}
    resp = client.post("/graphql", content_type="application/json", data=data)

    assert "errors" in resp.json()
    assert "Study must be specified" in resp.json()["errors"][0]["message"]
