import graphene
import django_filters
from graphene import relay, Field, String
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import OrderingFilter
from graphql import GraphQLError

from ..models import File, Version
from creator.files.nodes.version import VersionNode


class VersionFilter(django_filters.FilterSet):
    file_kf_id = django_filters.CharFilter(
        field_name="root_file__kf_id", lookup_expr="exact"
    )

    class Meta:
        model = Version
        fields = []

    order_by = OrderingFilter(fields=("created_at",))


class Query(object):
    version = relay.Node.Field(VersionNode, description="Get a version")
    version_by_kf_id = Field(
        VersionNode,
        kf_id=String(required=True),
        description="Get a version by its kf_id",
    )
    all_versions = DjangoFilterConnectionField(
        VersionNode,
        filterset_class=VersionFilter,
        description="List all versions",
    )

    def resolve_version_by_kf_id(self, info, kf_id):
        return VersionNode.get_node(info, kf_id)

    def resolve_all_versions(self, info, **kwargs):
        """
        If user is USER, only return the file versions from the studies
        which the user belongs to
        If user is ADMIN, return all file versions
        If user is unauthed, return no file versions
        """
        user = info.context.user
        if user.has_perm("files.list_all_version"):
            return Version.objects.all()

        # Only return files that the user is a member of
        if user.has_perm("files.view_my_version"):
            return Version.objects.filter(
                root_file__study__in=user.studies.all()
            )

        raise GraphQLError("Not allowed")
