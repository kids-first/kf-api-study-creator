from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.status.banners.models import Banner


class BannerNode(DjangoObjectType):
    class Meta:
        model = Banner
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        if not (user.has_perm("status.view_banner")):
            raise GraphQLError("Not allowed")

        try:
            banner = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Banner was not found")

        return banner
