import django_filters
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter

from creator.status.banners.nodes import BannerNode
from creator.status.banners.models import Banner


class BannerFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))
    started_before = django_filters.DateTimeFilter(
        field_name="start_date", lookup_expr="lt"
    )
    started_after = django_filters.DateTimeFilter(
        field_name="start_date", lookup_expr="gt"
    )
    ended_before = django_filters.DateTimeFilter(
        field_name="end_date", lookup_expr="lt"
    )
    ended_after = django_filters.DateTimeFilter(
        field_name="end_date", lookup_expr="gt"
    )

    class Meta:
        model = Banner
        fields = ["enabled"]


class Query(object):
    banner = relay.Node.Field(BannerNode, description="Get a single banner")
    all_banners = DjangoFilterConnectionField(
        BannerNode,
        filterset_class=BannerFilter,
        description="Get all banner",
    )

    def resolve_all_banners(self, info, **kwargs):
        """
        Return all banners
        """
        user = info.context.user

        if not user.has_perm("status.list_all_banner"):
            raise GraphQLError("Not allowed")

        return Banner.objects.all()
