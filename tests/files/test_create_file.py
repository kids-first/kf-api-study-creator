import pytest
import uuid
from django.contrib.auth import get_user_model
from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.studies.models import Study, Membership
from creator.files.models import Version

from creator.studies.factories import StudyFactory
from creator.files.factories import VersionFactory
from creator.data_templates.factories import TemplateVersionFactory

User = get_user_model()


CREATE_FILE = """
    mutation (
        $version: ID!,
        $name: String!,
        $description: String!,
        $fileType: FileType!,
        $study: ID
        $tags: [String]
        $templateVersion: ID
    ) {
        createFile(
          version: $version,
          name: $name,
          study: $study,
          description: $description,
          fileType: $fileType
          tags: $tags
          templateVersion: $templateVersion
        ) {
            file {
                id
                kfId
                name
                description
                fileType
                tags
                templateVersion { id  }
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


def test_create_file(db, clients):
    """
    Test the create file mutation
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    version = Version(size=123)
    version.save()
    template_version = TemplateVersionFactory()

    variables = {
        "version": to_global_id("VersionNode", version.pk),
        "name": "Test file",
        "study": to_global_id("StudyNode", study.pk),
        "description": "This is my test file",
        "fileType": "OTH",
        "tags": ["tag1", "tag2"],
        "templateVersion": to_global_id(
            "TemplateVersionNode", template_version.pk
        )
    }

    data = {"query": CREATE_FILE, "variables": variables}
    resp = client.post("/graphql", content_type="application/json", data=data)

    result = resp.json()["data"]["createFile"]["file"]
    assert result["id"]
    assert result["templateVersion"]


def test_study_does_not_exist(db, clients):
    """
    Test that error is returned if the provided study is not found.
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    version = VersionFactory(study=study)

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


def test_template_does_not_exist(db, clients):
    """
    Check that an error is returned if the provided template_version
    is not found.
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    version = Version(size=123)
    version.save()

    variables = {
        "version": to_global_id("VersionNode", version.pk),
        "name": "Test file",
        "study": to_global_id("StudyNode", study.pk),
        "description": "This is my test file",
        "fileType": "OTH",
        "tags": ["tag1", "tag2"],
        "templateVersion": to_global_id(
            "TemplateVersionNode", str(uuid.uuid4())
        )
    }

    data = {"query": CREATE_FILE, "variables": variables}
    resp = client.post("/graphql", content_type="application/json", data=data)

    assert "errors" in resp.json()
    assert "TemplateVersion" in resp.json()["errors"][0]["message"]
