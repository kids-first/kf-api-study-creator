from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter

from creator.{{ app_name }}.nodes import {{ model_name }}Node
from creator.{{ app_name }}.models import {{ model_name }}


class {{ model_name }}Filter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))

    class Meta:
        model = {{ model_name }}
        fields = []


class Query(object):
    {{ singular }} = relay.Node.Field({{ model_name }}Node, description="Get a single {{ singular }}")
    all_{{ plural }} = DjangoFilterConnectionField(
        {{ model_name }}Node,
        filterset_class={{ model_name }}Filter,
        description="Get all {{ plural }}",
    )

    def resolve_all_{{ app_name }}(self, info, **kwargs):
        """
        Return all {{ app_name }}
        """
        user = info.context.user

        if not user.has_perm("{{ app_name }}.list_all_{{ singular }}"):
            raise GraphQLError("Not allowed")

        return {{ model_name }}.objects.all()