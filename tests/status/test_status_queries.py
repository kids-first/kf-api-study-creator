import pytest

STATUS_QUERY = """
query {
    status {
        name
        commit
        version
        settings {
          dataserviceUrl
        }
        features {
          studyCreation
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
def test_query_status(db, clients, user_group, allowed):
    client = clients.get(user_group)

    resp = client.post(
        "/graphql",
        data={"query": STATUS_QUERY},
        content_type="application/json"
    )

    if allowed:
        assert resp.json()["data"] is not None
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
