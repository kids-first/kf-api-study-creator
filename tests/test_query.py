import pytest
from django.contrib.auth import get_user_model
from creator.studies.models import Study, Membership
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory

User = get_user_model()


def test_schema_query(client, db):
    query = """
        {__schema {
          types {
            name
            description
          }
        }}
    """
    query_data = {"query": query.strip()}
    resp = client.post(
        "/graphql", data=query_data, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "__schema" in resp.json()["data"]


def test_unauthed_study_query(db, clients):
    """
    Queries made with no authentication should return no studies
    """
    client = clients.get(None)
    studies = StudyFactory.create_batch(5)
    query = "{ allStudies { edges { node { name } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_my_studies_query(db, clients):
    """
    Test that only studies belonging to the user are returned
    """
    client = clients.get("Investigators")
    studies = StudyFactory.create_batch(5)
    user = User.objects.filter(groups__name="Investigators").first()
    Membership(collaborator=user, study=studies[0]).save()

    query = "{ allStudies { edges { node { name } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allStudies" in resp.json()["data"]
    assert len(resp.json()["data"]["allStudies"]["edges"]) == 1


def test_admin_studies_query(db, clients):
    """
    Test that only studies belonging to the user are returned
    """
    client = clients.get("Administrators")
    studies = StudyFactory.create_batch(5)

    query = "{ allStudies { edges { node { name } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allStudies" in resp.json()["data"]
    assert len(resp.json()["data"]["allStudies"]["edges"]) == 5


def test_unauthed_file_query(db, clients):
    """
    Queries made with no authentication should return no files
    """
    client = clients.get(None)

    query = "{ allFiles { edges { node { id } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_my_files_query(db, clients):
    """
    Test that only files under the studies belonging to the user are returned
    """
    client = clients.get("Investigators")
    study1 = StudyFactory(files=0)
    study2 = StudyFactory(files=0)
    file1 = FileFactory(study=study1)
    file2 = FileFactory(study=study2)
    user = User.objects.filter(groups__name="Investigators").first()
    Membership(collaborator=user, study=study1).save()

    query = "{ allFiles { edges { node { id } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allFiles" in resp.json()["data"]
    assert len(resp.json()["data"]["allFiles"]["edges"]) == 1


def test_admin_files_query(db, clients):
    """
    Test that all files are returned
    """
    client = clients.get("Administrators")
    study = StudyFactory(files=0)
    file = FileFactory(study=study)

    query = "{ allFiles { edges { node { id } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allFiles" in resp.json()["data"]
    assert len(resp.json()["data"]["allFiles"]["edges"]) == 1


def test_unauthed_version_query(db, clients):
    """
    Queries made with no authentication should return no file versions
    """
    client = clients.get(None)

    query = "{ allVersions { edges { node { id } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_my_versions_query(db, clients):
    """
    Test that only file versions under the studies belonging to the user
    are returned
    """
    client = clients.get("Investigators")
    study1 = StudyFactory(files=0)
    study2 = StudyFactory(files=0)
    file1 = FileFactory(study=study1)
    file2 = FileFactory(study=study2)
    user = User.objects.filter(groups__name="Investigators").first()
    Membership(collaborator=user, study=study1).save()

    query = "{ allVersions { edges { node { id } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allVersions" in resp.json()["data"]
    assert (
        len(resp.json()["data"]["allVersions"]["edges"])
        == file1.versions.count()
    )


def test_admin_versions_query(db, clients):
    """
    Test that all file versions are returned
    """
    client = clients.get("Administrators")
    study = StudyFactory(files=0)
    file = FileFactory(study=study)

    query = "{ allVersions { edges { node { id } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allVersions" in resp.json()["data"]
    assert (
        len(resp.json()["data"]["allVersions"]["edges"])
        == file.versions.count()
    )


def test_status_query(client):
    """
    Test that the status endpoint returns git info
    """
    query = """
    {
        status {
            commit name version
            features { studyCreation }
            settings { dataserviceUrl }
            queues
        }
    }"""
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "status" in resp.json()["data"]
    status = resp.json()["data"]["status"]
    assert status["name"] == "Kids First Study Creator"
    assert (
        status["version"].count("-") == 2 or status["version"].count(".") == 2
    )
    assert len(status["commit"]) == 7
    assert "features" in status
    assert status["settings"] is None
    assert status["queues"] is None
    assert "errors" in resp.json()
    assert len(resp.json()["errors"]) == 2


def test_admin_status_query(db, clients):
    """
    Test that an admin may see settings and queues variables
    """
    client = clients.get("Administrators")
    query = """
    {
        status {
            commit name version
            features { studyCreation }
            settings { dataserviceUrl }
            queues
        }
    }"""
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "status" in resp.json()["data"]
    status = resp.json()["data"]["status"]
    assert status["name"] == "Kids First Study Creator"
    assert (
        status["version"].count("-") == 2 or status["version"].count(".") == 2
    )
    assert len(status["commit"]) == 7
    assert "features" in status
    assert "queues" in status
    assert status["settings"]["dataserviceUrl"] == "http://dataservice"
    assert "errors" not in resp.json()
