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
