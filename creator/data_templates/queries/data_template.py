from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter

from creator.data_templates.nodes.data_template import DataTemplateNode
from creator.data_templates.models import DataTemplate


class DataTemplateFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_at",))

    class Meta:
        model = DataTemplate
        fields = []


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

        return DataTemplate.objects.all()
