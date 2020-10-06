from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.releases.models import Release


class ReleaseNode(DjangoObjectType):
    class Meta:
        model = Release
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        if not (user.has_perm("releases.view_release")):
            raise GraphQLError("Not allowed")

        try:
            release = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Releases was not found")

        return release
