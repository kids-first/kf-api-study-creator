import pytest
from creator.files.models import DevDownloadToken


@pytest.mark.parametrize(
    "user_type,expected",
    [("admin", True), ("service", True), ("user", False), (None, False)],
)
def test_list_dev_tokens(
    db, admin_client, service_client, user_client, client, user_type, expected
):
    """
    Test that only admins may list tokens
    """
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]

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
                }
            }
        }
    }
    """
    resp = api_client.post(
        "/graphql", content_type="application/json", data={"query": query}
    )
    assert resp.status_code == 200
    resp_body = resp.json()["data"]["allDevTokens"]
    if expected:
        assert len(resp_body["edges"]) == 2
    else:
        assert len(resp_body["edges"]) == 0


def test_download_with_header(db, client, prep_file):
    """
    Test that we may download a file when providing the download token in
    the Authorization header
    """
    token = DevDownloadToken(name="test token")
    token.save()
    expected_name = "attachment; filename*=UTF-8''manifest.txt"
    study_id, file_id, version_id = prep_file()

    resp = client.get(
        f"/download/study/{study_id}/file/{file_id}",
        HTTP_AUTHORIZATION=f"Token {token.token}",
    )
    assert resp.status_code == 200
    assert resp.get("Content-Disposition") == expected_name
    assert resp.content == b"aaa\nbbb\nccc\n"


def test_download_with_bad_header(db, client, prep_file):
    """
    Test that the download may not occur if the token in the header is invalid
    """
    study_id, file_id, version_id = prep_file()

    resp = client.get(
        f"/download/study/{study_id}/file/{file_id}",
        HTTP_AUTHORIZATION=f"Token abcabc",
    )
    assert resp.status_code == 401
    assert resp.get("Content-Disposition") is None


def test_download_with_no_token(db, client, prep_file):
    """
    Test that the download may not occur if no token is provided in the header
    or in the url.
    """
    study_id, file_id, version_id = prep_file()

    resp = client.get(f"/download/study/{study_id}/file/{file_id}")
    assert resp.status_code == 401
    assert resp.get("Content-Disposition") is None
