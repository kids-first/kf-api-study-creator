from pprint import pprint
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter, CharFilter

from creator.data_templates.nodes.data_template import DataTemplateNode
from creator.data_templates.models import DataTemplate


class DataTemplateFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_at", "modified_at"))
    organization_name = CharFilter(
        field_name="organization__name", lookup_expr="icontains"
    )

    class Meta:
        model = DataTemplate
        fields = {
            "organization": ["exact"],
        }


class Query(object):
    data_template = relay.Node.Field(
        DataTemplateNode, description="Get a single data_template"
    )
    all_data_templates = DjangoFilterConnectionField(
        DataTemplateNode,
        filterset_class=DataTemplateFilter,
        description="Get all data_templates",
    )

    def resolve_all_data_templates(self, info, **kwargs):
        """
        Return all data_templates
        """
        user = info.context.user

        if not user.has_perm("data_templates.list_all_datatemplate"):
            raise GraphQLError("Not allowed")

        pprint(kwargs)
        return DataTemplate.objects.all()
