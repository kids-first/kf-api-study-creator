import uuid
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model

from creator.organizations.factories import OrganizationFactory
from creator.storage_backends.models import StorageBackend

User = get_user_model()

CREATE_STORAGE_BACKEND = """
mutation ($input: CreateStorageBackendInput!) {
    createStorageBackend(input: $input) {
        storageBackend {
            id
            createdAt
            name
        }
    }
}
"""

UPDATE_STORAGE_BACKEND = """
mutation ($id: ID!, $input: UpdateDataReviewInput!) {
    updateStorageBackend(id: $id, input: $input) {
        dataReview {
            id
            createdAt
            name
        }
    }
}
"""


def test_create_storage_backend(db, permission_client):
    """
    Test that new storage backends may be created.
    """
    user, client = permission_client(["add_storagebackend"])
    organization = OrganizationFactory()

    variables = {
        "input": {
            "name": "My Storage",
            "bucket": "data-storage-1",
            "prefix": "",
            "organization": to_global_id("OrganizationNode", organization.pk),
        }
    }

    resp = client.post(
        "/graphql",
        data={"query": CREATE_STORAGE_BACKEND, "variables": variables},
        content_type="application/json",
    )

    assert (
        resp.json()["data"]["createStorageBackend"]["storageBackend"]["name"]
        == "My Storage"
    )
    assert StorageBackend.objects.filter(name="My Storage").exists()


def test_create_storage_backend_not_allowed(db, permission_client):
    """
    Check that storage backends may not be created without permission.
    """
    user, client = permission_client([])
    organization = OrganizationFactory()

    variables = {
        "input": {
            "name": "My Storage",
            "bucket": "data-storage-1",
            "prefix": "",
            "organization": to_global_id("OrganizationNode", organization.pk),
        }
    }

    resp = client.post(
        "/graphql",
        data={"query": CREATE_STORAGE_BACKEND, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Not allowed" in resp.json()["errors"][0]["message"]


def test_create_storage_backend_in_my_org(db, permission_client):
    """
    Check that a user may create a storage backend in their organization.
    """
    user, client = permission_client(["add_my_org_storagebackend"])
    organization = OrganizationFactory()
    user.organizations.add(organization)

    variables = {
        "input": {
            "name": "My Storage",
            "bucket": "data-storage-1",
            "prefix": "",
            "organization": to_global_id("OrganizationNode", organization.pk),
        }
    }

    resp = client.post(
        "/graphql",
        data={"query": CREATE_STORAGE_BACKEND, "variables": variables},
        content_type="application/json",
    )

    assert (
        resp.json()["data"]["createStorageBackend"]["storageBackend"]["name"]
        == "My Storage"
    )
    assert StorageBackend.objects.filter(name="My Storage").exists()


def test_create_storage_backend_outside_my_org(db, permission_client):
    """
    Ensure that a user may not create a storage backend for an organization
    they do not belong to.
    """
    user, client = permission_client(["add_my_org_storagebackend"])
    organization = OrganizationFactory()

    variables = {
        "input": {
            "name": "My Storage",
            "bucket": "data-storage-1",
            "prefix": "",
            "organization": to_global_id("OrganizationNode", organization.pk),
        }
    }

    resp = client.post(
        "/graphql",
        data={"query": CREATE_STORAGE_BACKEND, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "Not allowed" in resp.json()["errors"][0]["message"]


def test_create_storage_backend_org_does_not_exist(db, permission_client):
    """
    Check that error is returned if the organization does not exist
    """
    user, client = permission_client(["add_storagebackend"])

    variables = {
        "input": {
            "name": "My Storage",
            "bucket": "data-storage-1",
            "prefix": "",
            "organization": to_global_id("OrganizationNode", uuid.uuid4()),
        }
    }

    resp = client.post(
        "/graphql",
        data={"query": CREATE_STORAGE_BACKEND, "variables": variables},
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert "not found" in resp.json()["errors"][0]["message"]
