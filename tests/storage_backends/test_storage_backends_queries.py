from graphql_relay import to_global_id
from django.contrib.auth import get_user_model
from creator.storage_backends.factories import StorageBackendFactory

User = get_user_model()

STORAGE_BACKEND = """
query ($id: ID!) {
    storageBackend(id: $id) {
        id
        createdAt
        name
    }
}
"""

ALL_STORAGE_BACKENDS = """
query {
    allStorageBackends {
        edges {
            node {
                id
                createdAt
                name
            }
        }
    }
}
"""


def test_query_storage_backend(db, permission_client):
    """
    Test that a single storage backend may be retrieved given that the user
    has permission to view any storage backend
    """
    user, client = permission_client(["view_storagebackend"])
    storage_backend = StorageBackendFactory()

    variables = {"id": to_global_id("StorageBackendNode", storage_backend.pk)}
    resp = client.post(
        "/graphql",
        data={"query": STORAGE_BACKEND, "variables": variables},
        content_type="application/json",
    )

    assert "storageBackend" in resp.json()["data"]
    result = resp.json()["data"]["storageBackend"]
    assert result["name"] == storage_backend.name


def test_query_storage_backend_not_allowed(db, permission_client):
    """
    Test that a storage backend may not be retrieved if the user has no
    permissions.
    """
    user, client = permission_client([])
    storage_backend = StorageBackendFactory()

    variables = {"id": to_global_id("StorageBackendNode", storage_backend.pk)}
    resp = client.post(
        "/graphql",
        data={"query": STORAGE_BACKEND, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Not allowed" in resp.json()["errors"][0]["message"]


def test_query_storage_backend_owned_by_users_org(db, permission_client):
    """
    Test that a single storage backend may be retrieved if the user may view
    the organizations backends and the requested backend is in the same
    organization as the user.
    """
    user, client = permission_client(["view_my_org_storagebackend"])
    storage_backend = StorageBackendFactory()
    user.organizations.add(storage_backend.organization)
    user.save()

    variables = {"id": to_global_id("StorageBackendNode", storage_backend.pk)}
    resp = client.post(
        "/graphql",
        data={"query": STORAGE_BACKEND, "variables": variables},
        content_type="application/json",
    )

    assert "storageBackend" in resp.json()["data"]
    result = resp.json()["data"]["storageBackend"]
    assert result["name"] == storage_backend.name


def test_query_storage_backend_not_owned_by_users_org(db, permission_client):
    """
    Test that a storage backend may not be retrieved if the user may see their
    own organization's backends but they do not belong to the organization
    which owns the backend they are requesting.
    """
    user, client = permission_client(["view_my_org_storagebackend"])
    storage_backend = StorageBackendFactory()

    variables = {"id": to_global_id("StorageBackendNode", storage_backend.pk)}
    resp = client.post(
        "/graphql",
        data={"query": STORAGE_BACKEND, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Not allowed" in resp.json()["errors"][0]["message"]


def test_query_all_storage_backends(db, permission_client):
    """
    Check that a priviledged user may list all storage backends
    """
    user, client = permission_client(["list_all_storagebackend"])
    StorageBackendFactory.create_batch(5)

    resp = client.post(
        "/graphql",
        data={"query": ALL_STORAGE_BACKENDS},
        content_type="application/json",
    )

    assert len(resp.json()["data"]["allStorageBackends"]["edges"]) == 5


def test_query_all_storage_backends_in_my_org(db, permission_client):
    """
    Check that a user may only see storage backends that belong to their
    organizations.
    """
    user, client = permission_client(["list_all_my_org_storagebackend"])
    storage_backends = StorageBackendFactory.create_batch(5)
    user.organizations.set(
        [storage_backends[0].organization, storage_backends[1].organization]
    )

    resp = client.post(
        "/graphql",
        data={"query": ALL_STORAGE_BACKENDS},
        content_type="application/json",
    )

    assert len(resp.json()["data"]["allStorageBackends"]["edges"]) == 2
