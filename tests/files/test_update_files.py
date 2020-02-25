import pytest

update_query = """
mutation (
    $kfId:String!,
    $description: String!,
    $name: String!,
    $fileType: FileFileType!
    $tags: [String]
) {
    updateFile(
        kfId: $kfId,
        name: $name,
        description:$description,
        fileType: $fileType
        tags: $tags
    ) {
        file { id kfId description name fileType tags }
    }
}
"""


def test_unauthed_file_mutation_query(client, db, prep_file):
    """
    File mutations are not allowed without authentication
    """
    (_, file_id, _) = prep_file()
    query = update_query
    variables = {
        "kfId": file_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["updateFile"] is None
    expected_error = "Not authenticated to mutate a file."
    assert resp.json()["errors"][0]["message"] == expected_error


def test_my_file_mutation_query(user_client, db, prep_file):
    """
    File mutations are allowed on the files under the studies that
    the user belongs to
    """
    (_, file_id, _) = prep_file(authed=True)
    query = update_query
    variables = {
        "kfId": file_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
        "tags": ["tag1", "tag2"],
    }
    resp = user_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    resp_file = resp.json()["data"]["updateFile"]["file"]
    assert resp_file["name"] == "New name"
    assert resp_file["description"] == "New description"
    assert resp_file["tags"] == ["tag1", "tag2"]


def test_not_my_file_mutation_query(user_client, db, prep_file):
    """
    File mutations are not allowed on the files under the studies that
    the user does not belong to
    """
    (_, file_id, _) = prep_file()
    query = update_query
    variables = {
        "kfId": file_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
    }
    resp = user_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["updateFile"] is None
    expected_error = "Not authenticated to mutate a file."
    assert resp.json()["errors"][0]["message"] == expected_error


def test_admin_file_mutation_query(admin_client, db, prep_file):
    """
    File mutations are allowed on any files for admin user
    """
    (_, file_id, _) = prep_file()
    query = update_query
    variables = {
        "kfId": file_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
        "tags": ["tag1", "tag2"],
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    resp_file = resp.json()["data"]["updateFile"]["file"]
    assert resp_file["name"] == "New name"
    assert resp_file["description"] == "New description"
    assert resp_file["tags"] == ["tag1", "tag2"]
