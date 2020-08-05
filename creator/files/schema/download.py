import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError

from creator.files.models import DevDownloadToken


class DevDownloadTokenNode(DjangoObjectType):
    token = graphene.String()

    class Meta:
        model = DevDownloadToken
        interfaces = (relay.Node,)
        filter_fields = []

    def resolve_token(self, info):
        """
        Return an obscured token with only the first four characters exposed,
        unless the token is being returned in response to a new token mutation.
        """
        if info.path == ["createDevToken", "token", "token"]:
            return self.token
        return self.token[:4] + "*" * (len(self.token) - 4)


class Query:
    all_dev_tokens = DjangoFilterConnectionField(
        DevDownloadTokenNode, description="Get all developer tokens"
    )

    def resolve_all_dev_tokens(self, info, **kwargs):
        """
        If user is admin, return all tokens, otherwise return none
        """
        user = info.context.user
        if not user.has_perm("files.view_downloadtoken"):
            raise GraphQLError("Not allowed")

        return DevDownloadToken.objects.all()
