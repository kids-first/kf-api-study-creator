from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter

from creator.releases.nodes import ReleaseNode
from creator.releases.models import Release


class ReleaseFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))

    class Meta:
        model = Release
        fields = []


class Query(object):
    release = relay.Node.Field(ReleaseNode, description="Get a single release")
    all_releases = DjangoFilterConnectionField(
        ReleaseNode,
        filterset_class=ReleaseFilter,
        description="Get all releases",
    )

    def resolve_all_releases(self, info, **kwargs):
        """
        Return all releases
        """
        user = info.context.user

        if not user.has_perm("releases.list_all_release"):
            raise GraphQLError("Not allowed")

        return Release.objects.all()
