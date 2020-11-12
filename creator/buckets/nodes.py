from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from creator.buckets.models import Bucket, BucketInventory
from creator.buckets.filters import BucketFilter, BucketInventoryFilter


class BucketNode(DjangoObjectType):
    inventories = DjangoFilterConnectionField(
        "creator.buckets.nodes.BucketInventoryNode",
        filterset_class=BucketInventoryFilter,
        description="List all bucket inventories for this bucket",
    )

    class Meta:
        model = Bucket
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, name):
        """
        Only return bucket if user is admin
        """
        user = info.context.user
        if not user.has_perm("buckets.view_bucket"):
            raise GraphQLError("Not allowed")

        try:
            return cls._meta.model.objects.get(name=name)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Bucket not found")

        return None


class BucketInventoryNode(DjangoObjectType):
    class Meta:
        model = BucketInventory
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        if not (user.has_perm("bucket_inventories.view_bucketinventory")):
            raise GraphQLError("Not allowed")

        try:
            bucket_inventory = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Bucket Inventory was not found")

        return bucket_inventory
