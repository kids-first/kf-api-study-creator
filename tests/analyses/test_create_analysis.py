import pytest
from graphql_relay import to_global_id
from moto import mock_s3
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory
from creator.files.models import Version
from creator.analyses.models import Analysis


CREATE_ANALYSIS_MUTATION = """
mutation runAnalysis($version: ID!) {
    createAnalysis(version: $version) {
        analysis {
            creator {
                username
            }
            version {
                fileName
            }
            columns
            knownFormat
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
def test_create_analysis_mutation(db, clients, user_group, allowed):
    """
    Test that analyses are properly controlled by permissions
    """
    study = StudyFactory(kf_id="SD_00000000")
    file = FileFactory(study=study)
    version_id = to_global_id("VersionNode", file.versions.first().kf_id)

    client = clients.get(user_group)
    variables = {"version": version_id}

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_ANALYSIS_MUTATION, "variables": variables},
    )

    if allowed:
        resp_body = resp.json()["data"]["createAnalysis"]["analysis"]
        resp_body = (
            resp.json()["data"]["createAnalysis"]["analysis"]["knownFormat"]
            is True
        )
        assert Analysis.objects.count() == 1
    else:
        assert Analysis.objects.count() == 0
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@mock_s3
def test_create_analysis_s3_study_id(
    db, clients, upload_version, tmp_uploads_s3
):
    """
    Test that analysis can be generated from objects in a study bucket.
    """
    client = clients.get("Administrators")

    study = StudyFactory(kf_id="SD_00000000")
    file = FileFactory(study=study)

    bucket = tmp_uploads_s3(study.bucket)

    resp = upload_version(
        "SD_ME0WME0W/FV_4DP2P2Y2_clinical.csv",
        study_id=study.kf_id,
        client=client,
    )
    version_id = resp.json()["data"]["createVersion"]["version"]["id"]

    variables = {"version": version_id}

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_ANALYSIS_MUTATION, "variables": variables},
    )

    resp_body = resp.json()["data"]["createAnalysis"]["analysis"]
    resp_body = (
        resp.json()["data"]["createAnalysis"]["analysis"]["knownFormat"]
        is True
    )
    assert Analysis.objects.count() == 1


@mock_s3
def test_create_analysis_s3_file_id(db, clients, upload_file, tmp_uploads_s3):
    """
    Test that a version with only a root file and no linked study may be
    analyzed.
    """
    client = clients.get("Administrators")

    study = StudyFactory(kf_id="SD_00000000")
    file = FileFactory(study=study)

    bucket = tmp_uploads_s3(study.bucket)

    resp = upload_file(
        study.kf_id, "SD_ME0WME0W/FV_4DP2P2Y2_clinical.csv", client
    )
    version_id = resp.json()["data"]["createFile"]["file"]["versions"][
        "edges"
    ][0]["node"]["id"]
    kf_id = resp.json()["data"]["createFile"]["file"]["versions"]["edges"][0][
        "node"
    ]["kfId"]

    version = Version.objects.get(kf_id=kf_id)
    version.study = None
    version.save()

    variables = {"version": version_id}

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_ANALYSIS_MUTATION, "variables": variables},
    )
    resp_body = resp.json()["data"]["createAnalysis"]["analysis"]
    resp_body = (
        resp.json()["data"]["createAnalysis"]["analysis"]["knownFormat"]
        is True
    )
    assert Analysis.objects.count() == 1


@mock_s3
def test_create_analysis_s3_no_study_or_file(
    db, clients, upload_version, tmp_uploads_s3
):
    """
    Test that a version without a study or root file may not be analyzed.
    """
    client = clients.get("Administrators")

    study = StudyFactory(kf_id="SD_00000000")
    file = FileFactory(study=study)

    bucket = tmp_uploads_s3(study.bucket)

    resp = upload_version(
        "SD_ME0WME0W/FV_4DP2P2Y2_clinical.csv",
        study_id=study.kf_id,
        client=client,
    )
    version_id = resp.json()["data"]["createVersion"]["version"]["id"]
    kf_id = resp.json()["data"]["createVersion"]["version"]["kfId"]

    version = Version.objects.get(kf_id=kf_id)
    version.study = None
    version.save()

    variables = {"version": version_id}

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_ANALYSIS_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert "must be part of a study" in resp.json()["errors"][0]["message"]
