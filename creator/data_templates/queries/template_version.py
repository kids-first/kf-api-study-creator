from graphene import relay
from graphene_django.filter import (
    DjangoFilterConnectionField,
    GlobalIDMultipleChoiceFilter,
)
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter, CharFilter

from creator.data_templates.nodes.template_version import TemplateVersionNode
from creator.data_templates.models import TemplateVersion


class TemplateVersionFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_at", "modified_at"))
    studies = GlobalIDMultipleChoiceFilter(field_name="studies__kf_id")

    class Meta:
        model = TemplateVersion
        fields = []


class Query(object):
    template_version = relay.Node.Field(
        TemplateVersionNode, description="Get a single template_version"
    )
    all_template_versions = DjangoFilterConnectionField(
        TemplateVersionNode,
        filterset_class=TemplateVersionFilter,
        description="Get all template_versions",
    )

    def resolve_all_template_versions(self, info, **kwargs):
        """
        Return all template_versions
        """
        user = info.context.user

        if not user.has_perm("data_templates.list_all_datatemplate"):
            raise GraphQLError("Not allowed")

        return TemplateVersion.objects.all()
