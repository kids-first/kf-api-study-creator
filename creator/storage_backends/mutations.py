import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id

from creator.storage_backends.nodes import StorageBackendNode
from creator.storage_backends.models import StorageBackend
from creator.organizations.models import Organization


class CreateStorageBackendInput(graphene.InputObjectType):
    """Parameters used when creating a new storage backend"""

    name = graphene.String(
        required=True, description="The display name of the storage backend"
    )
    organization = graphene.ID(
        required=True,
        description="The ID organization to add the storage backend to",
    )
    bucket = graphene.String(
        required=True,
        description="The name of the bucket in AWS",
    )
    prefix = graphene.String(
        description="The prefix within the bucket to use as the root",
    )
    access_key = graphene.String(
        description="The AWS access key",
    )
    secret_key = graphene.String(
        description="The AWS secret key",
    )


class CreateStorageBackendMutation(graphene.Mutation):
    """Creates a new storage backend"""

    class Arguments:
        input = CreateStorageBackendInput(
            required=True, description="Attributes for the new storage backend"
        )

    storage_backend = graphene.Field(StorageBackendNode)

    def mutate(self, info, input):
        """
        Creates a new storage_backend.
        """
        user = info.context.user

        # Check if organization exists
        _, organization_id = from_global_id(input.get("organization"))
        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            raise GraphQLError(f"Organization {organization_id} not found.")

        # Check permissions
        if not (
            user.has_perm("storage_backends.add_storagebackend")
            or (
                user.has_perm("storage_backends.add_my_org_storagebackend")
                and user.organizations.filter(pk=organization.pk).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        storage_backend = StorageBackend(
            name=input.get("name"),
            bucket=input.get("bucket"),
            prefix=input.get("prefix"),
            access_key=input.get("access_key"),
            secret_key=input.get("secret_key"),
            organization=organization,
        )
        storage_backend.save()

        return CreateStorageBackendMutation(storage_backend=storage_backend)


class UpdateStorageBackendInput(graphene.InputObjectType):
    """Parameters used when creating a new storage backend"""

    name = graphene.String(
        required=True, description="The display name of the storage backend"
    )
    access_key = graphene.String(
        description="The AWS access key",
    )
    secret_key = graphene.String(
        description="The AWS secret key",
    )


class UpdateStorageBackendMutation(graphene.Mutation):
    """Update an existing storage backend"""

    class Arguments:
        id = graphene.ID(
            required=True,
            description="The ID of the storage backend to update",
        )
        input = UpdateStorageBackendInput(
            required=True, description="Attributes for the storage backend"
        )

    storage_backend = graphene.Field(StorageBackendNode)

    def mutate(self, info, id, input):
        """
        Updates an existing storage backend
        """
        user = info.context.user

        model, node_id = from_global_id(id)
        try:
            storage_backend = StorageBackend.objects.get(pk=node_id)
        except StorageBackend.DoesNotExist:
            raise GraphQLError("StorageBackend was not found")

        # Check permissions
        if not (user.has_perm("storage_backends.change_storage_backend")):
            raise GraphQLError("Not allowed")

        return UpdateStorageBackendMutation(storage_backend=storage_backend)


class Mutation:
    """Mutations for storage backends"""

    create_storage_backend = CreateStorageBackendMutation.Field(
        description="Create a new storage backend"
    )
    update_storage_backend = UpdateStorageBackendMutation.Field(
        description="Update a given storage backend"
    )
