import pytest
from creator.files.models import File, Version
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory, VersionFactory


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
def test_delete_file_mutation(db, clients, user_group, allowed, mocker):
    """
    Test that a file may be deleted through the deleteFile mutation.
    """

    client = clients.get(user_group)
    study = StudyFactory()
    file = FileFactory(study=study, versions=None)
    version = VersionFactory(root_file=file)

    version_counts = Version.objects.count()

    query = """
    mutation ($kfId: String!) {
        deleteFile(kfId: $kfId) {
            success
        }
    }
    """
    variables = {"kfId": file.kf_id}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    if allowed:
        resp_body = resp.json()["data"]["deleteFile"]
        assert resp.status_code == 200
        assert resp_body["success"] is True
        assert Version.objects.count() == 0
        assert File.objects.count() == 0
    else:
        assert resp.status_code == 200
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert Version.objects.count() == version_counts
        assert File.objects.count() == 1
