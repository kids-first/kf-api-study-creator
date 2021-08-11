from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.storage_backends.models import StorageBackend


class StorageBackendNode(DjangoObjectType):
    class Meta:
        model = StorageBackend
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        try:
            storage_backend = cls._meta.model.objects.get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("StorageBackend was not found")

        if not (
            user.has_perm("storage_backends.view_storagebackend")
            or (
                user.has_perm("storage_backends.view_my_org_storagebackend")
                and user.organizations.filter(
                    pk=storage_backend.organization.pk
                ).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        return storage_backend
