from graphene import relay, Boolean
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.data_templates.models import TemplateVersion


class TemplateVersionNode(DjangoObjectType):
    released = Boolean(source="released")

    class Meta:
        model = TemplateVersion
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        if not (user.has_perm("data_templates.view_datatemplate")):
            raise GraphQLError("Not allowed")

        try:
            template_version = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError(f"TemplateVersion {id} does not exist")

        return template_version
