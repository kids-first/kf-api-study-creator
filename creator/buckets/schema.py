from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, OrderingFilter
from graphql import GraphQLError

from creator.buckets.models import Bucket
from creator.buckets.mutations import Mutation


class BucketFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on"))

    class Meta:
        model = Bucket
        fields = ["name", "deleted", "study"]


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


class Query(object):
    bucket = relay.Node.Field(BucketNode, description="Get a single bucket")
    all_buckets = DjangoFilterConnectionField(
        BucketNode, filterset_class=BucketFilter, description="Get all buckets"
    )

    def resolve_all_buckets(self, info, **kwargs):
        """
        Return all buckets if the user has the 'list_all_bucket' permission
        """
        user = info.context.user
        if not user.has_perm("buckets.list_all_bucket"):
            raise GraphQLError("Not allowed")

        qs = Bucket.objects
        if kwargs.get("study") == "":
            qs = qs.filter(study=None)
        return qs.all()
