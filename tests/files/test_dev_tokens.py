import pytest
from django.http.response import HttpResponse
from django.contrib.auth import get_user_model
from creator.files.models import File, Version, DevDownloadToken
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
def test_list_dev_tokens(db, clients, user_group, allowed):
    """
    Test that only admins may list tokens and only the first four characters
    are returned.
    """
    client = clients.get(user_group)

    token1 = DevDownloadToken(name="test token 1")
    token2 = DevDownloadToken(name="test token 2")
    token1.save()
    token2.save()

    query = """
    {
        allDevTokens {
            edges {
                node {
                    id
                    name
                    token
                    createdAt
                    creator {
                        email
                    }
                }
            }
        }
    }
    """
    resp = client.post(
        "/graphql", content_type="application/json", data={"query": query}
    )
    assert resp.status_code == 200
    if allowed:
        resp_body = resp.json()["data"]["allDevTokens"]
        assert len(resp_body["edges"]) == 2
        assert resp_body["edges"][0]["node"]["token"].endswith("*" * 23)
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_create_dev_download_token_mutation(
    db, clients, versions, user_group, allowed
):
    """
    Test that a dev download token may created by an admin.
    """
    client = clients.get(user_group)
    study, file, version = versions

    version_counts = Version.objects.count()

    query = """
    mutation ($name: String!) {
        createDevToken(name: $name) {
            token {
                id
                name
                token
                createdAt
            }
        }
    }
    """

    variables = {"name": "test token"}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    if allowed:
        assert resp.status_code == 200
        resp_body = resp.json()["data"]["createDevToken"]
        assert "token" in resp_body
        token = resp_body["token"]
        assert "name" in token
        assert "token" in token
        assert "createdAt" in token
        url = File.objects.first().path
        resp = client.get(f'{url}?token={token["token"]}')
        assert resp.status_code == 200
    else:
        assert resp.status_code == 200
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert Version.objects.count() == version_counts
        assert File.objects.count() == 1


def test_dev_token_unique_name(db, clients):
    """
    Test that dev tokens may not be created with the same name
    """
    query = """
    mutation ($name: String!) {
        createDevToken(name: $name) {
            token {
                id
                name
                token
                createdAt
            }
        }
    }
    """
    client = clients.get("Administrators")
    variables = {"name": "test token"}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    assert resp.status_code == 200
    resp_body = resp.json()["data"]["createDevToken"]
    assert "token" in resp_body
    token = resp_body["token"]
    assert "name" in token
    assert "token" in token
    assert "createdAt" in token

    # Try to make another token with the same name
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    resp_body = resp.json()
    assert "errors" in resp_body
    assert resp_body["errors"][0]["message"].endswith("already exists.")


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
def test_delete_dev_token_mutation(
    db, clients, prep_file, user_group, allowed
):
    """
    Test that a dev token  may be deleted through the deleteDevToken mutation.
    Only admin users may delete a token
    """
    client = clients.get(user_group)
    token = DevDownloadToken(name="test token")
    token.save()
    query = """
    mutation ($name: String!) {
        deleteDevToken(name: $name) {
            success
        }
    }
    """
    variables = {"name": token.name}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    assert resp.status_code == 200
    if allowed:
        resp_body = resp.json()["data"]["deleteDevToken"]
        assert resp_body["success"] is True
        assert DevDownloadToken.objects.count() == 0
    else:
        assert resp.status_code == 200
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert DevDownloadToken.objects.count() == 1


def test_download_with_header(db, client, mocker):
    """
    Test that we may download a file when providing the download token in
    the Authorization header
    """
    token = DevDownloadToken(name="test token")
    token.save()
    study = StudyFactory()
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")
    version.key = HttpResponse(open("tests/data/data.csv"))
    mock_resp = mocker.patch("creator.files.views._resolve_version")
    mock_resp.return_value = (file, version)

    expected_name = (
        f"attachment; filename*=UTF-8''{version.kf_id}_{version.file_name}"
    )

    resp = client.get(
        f"/download/study/{study.kf_id}/file/{file.kf_id}",
        HTTP_AUTHORIZATION=f"Token {token.token}",
    )
    assert resp.status_code == 200
    assert resp.get("Content-Disposition") == expected_name
    assert resp.content == b"aaa,bbb,ccc\nddd,eee,fff\n"


def test_download_with_bad_header(db, client, prep_file):
    """
    Test that the download may not occur if the token in the header is invalid
    """
    study = StudyFactory()
    file = FileFactory(study=study)

    resp = client.get(
        f"/download/study/{study.kf_id}/file/{file.kf_id}",
        HTTP_AUTHORIZATION=f"Token abcabc",
    )
    assert resp.status_code == 401
    assert resp.get("Content-Disposition") is None


def test_download_with_no_token(db, client, prep_file):
    """
    Test that the download may not occur if no token is provided in the header
    or in the url.
    """
    study = StudyFactory()
    file = FileFactory(study=study)

    resp = client.get(f"/download/study/{study.kf_id}/file/{file.kf_id}")
    assert resp.status_code == 401
    assert resp.get("Content-Disposition") is None
