import pytest
from creator.studies.factories import StudyFactory
from creator.studies.models import Study


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


def test_unauthed_study_query(client, db):
    """
    Queries made with no authentication should return no studies
    """
    studies = StudyFactory.create_batch(5)
    query = "{ allStudies { edges { node { name } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allStudies" in resp.json()["data"]
    assert len(resp.json()["data"]["allStudies"]["edges"]) == 0


def test_my_studies_query(user_client, db):
    """
    Test that only studies belonging to the user are returned
    """
    studies = StudyFactory.create_batch(5)
    # Make the user's study
    study = Study(kf_id="SD_00000000", external_id="Test")
    study.save()

    query = "{ allStudies { edges { node { name } } } }"
    resp = user_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allStudies" in resp.json()["data"]
    assert len(resp.json()["data"]["allStudies"]["edges"]) == 1


def test_admin_studies_query(admin_client, db):
    """
    Test that only studies belonging to the user are returned
    """
    studies = StudyFactory.create_batch(5)

    query = "{ allStudies { edges { node { name } } } }"
    resp = admin_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allStudies" in resp.json()["data"]
    assert len(resp.json()["data"]["allStudies"]["edges"]) == 5


def test_unauthed_file_query(client, db, prep_file):
    """
    Queries made with no authentication should return no files
    """
    prep_file()

    query = "{ allFiles { edges { node { id } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allFiles" in resp.json()["data"]
    assert len(resp.json()["data"]["allFiles"]["edges"]) == 0


def test_my_files_query(user_client, db, prep_file):
    """
    Test that only files under the studies belonging to the user are returned
    """
    prep_file()
    prep_file(authed=True)

    query = "{ allFiles { edges { node { id } } } }"
    resp = user_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allFiles" in resp.json()["data"]
    assert len(resp.json()["data"]["allFiles"]["edges"]) == 1


def test_admin_files_query(admin_client, db, prep_file):
    """
    Test that all files are returned
    """
    prep_file()

    query = "{ allFiles { edges { node { id } } } }"
    resp = admin_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allFiles" in resp.json()["data"]
    assert len(resp.json()["data"]["allFiles"]["edges"]) == 1


def test_unauthed_version_query(client, db, prep_file):
    """
    Queries made with no authentication should return no file versions
    """
    prep_file()

    query = "{ allVersions { edges { node { id } } } }"
    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allVersions" in resp.json()["data"]
    assert len(resp.json()["data"]["allVersions"]["edges"]) == 0


def test_my_versions_query(user_client, db, prep_file):
    """
    Test that only file versions under the studies belonging to the user
    are returned
    """
    prep_file()
    prep_file(authed=True)

    query = "{ allVersions { edges { node { id } } } }"
    resp = user_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allVersions" in resp.json()["data"]
    assert len(resp.json()["data"]["allVersions"]["edges"]) == 1


def test_admin_versions_query(admin_client, db, prep_file):
    """
    Test that all file versions are returned
    """
    prep_file()

    query = "{ allVersions { edges { node { id } } } }"
    resp = admin_client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allVersions" in resp.json()["data"]
    assert len(resp.json()["data"]["allVersions"]["edges"]) == 1


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
            jobs { edges { node { id name } } }
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
    assert len(resp.json()["errors"]) == 3


def test_admin_status_query(db, admin_client):
    """
    Test that an admin may see settings and queues variables
    """
    query = """
    {
        status {
            commit name version
            features { studyCreation }
            settings { dataserviceUrl }
            queues
            jobs { edges { node { id name } } }
        }
    }"""
    resp = admin_client.post(
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
    assert "jobs" in status
    assert status["settings"]["dataserviceUrl"] == "http://dataservice"
    assert "errors" not in resp.json()
