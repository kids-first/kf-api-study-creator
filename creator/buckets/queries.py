from graphene import relay
from graphql import GraphQLError
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, OrderingFilter

from creator.buckets.nodes import BucketNode
from creator.buckets.models import Bucket


class BucketFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on"))

    class Meta:
        model = Bucket
        fields = ["name", "deleted", "study"]


class Query:
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
