from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.buckets.models import Bucket


class BucketNode(DjangoObjectType):
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
