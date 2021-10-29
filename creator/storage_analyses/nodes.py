from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from creator.events.schema import EventNode, EventFilter

from creator.storage_analyses.models import StorageAnalysis


class StorageAnalysisNode(DjangoObjectType):
    events = DjangoFilterConnectionField(
        EventNode, filterset_class=EventFilter, description="List all events"
    )

    class Meta:
        model = StorageAnalysis
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        try:
            storage_analysis = cls._meta.model.objects.get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("StorageAnalysis does not exist")

        if not (
            user.has_perm("storage_analyses.view_storageanalysis")
            and user.studies.filter(
                kf_id=storage_analysis.study.kf_id
            ).exists()
        ):
            raise GraphQLError("Not allowed")

        return storage_analysis
