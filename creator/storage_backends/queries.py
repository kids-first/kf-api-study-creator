from graphene import relay
from graphql import GraphQLError
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, OrderingFilter

from creator.storage_backends.nodes import StorageBackendNode
from creator.storage_backends.models import StorageBackend


class StorageBackendFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))

    class Meta:
        model = StorageBackend
        fields = []


class Query(object):
    storage_backend = relay.Node.Field(
        StorageBackendNode, description="Get a single storage backend"
    )
    all_storage_backends = DjangoFilterConnectionField(
        StorageBackendNode,
        filterset_class=StorageBackendFilter,
        description="Get all storage backends",
    )

    def resolve_all_storage_backends(self, info, **kwargs):
        """
        Return all storage backends
        """
        user = info.context.user

        if user.has_perm("storage_backends.list_all_storagebackend"):
            return StorageBackend.objects.all()
        elif user.has_perm("storage_backends.list_all_my_org_storagebackend"):
            return StorageBackend.objects.filter(
                organization__in=user.organizations.all()
            )

        raise GraphQLError("Not allowed")
