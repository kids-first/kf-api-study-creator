from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.{{ app_name }}.models import {{ model_name }}


class {{ model_name }}Node(DjangoObjectType):
    class Meta:
        model = {{ model_name }}
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        if not (user.has_perm("{{ app_name }}.view_{{ permission_singular }}")):
            raise GraphQLError("Not allowed")

        try:
            {{ singular }} = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("{{ camel_case_app_name }} was not found")

        return {{ singular }}
