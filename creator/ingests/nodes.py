from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.ingests.models import IngestRun


class IngestRunNode(DjangoObjectType):
    class Meta:
        model = IngestRun
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        if not (user.has_perm("ingests.view_ingestrun")):
            raise GraphQLError("Not allowed")

        try:
            ingest = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Ingests was not found")

        return ingest
