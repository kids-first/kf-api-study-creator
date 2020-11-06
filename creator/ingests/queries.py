from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter

from creator.ingests.nodes import IngestRunNode
from creator.ingests.models import IngestRun


class IngestRunFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))

    class Meta:
        model = IngestRun
        fields = []


class Query(object):
    ingest_run = relay.Node.Field(
        IngestRunNode, description="Get a single ingest run"
    )
    all_ingest_runs = DjangoFilterConnectionField(
        IngestRunNode,
        filterset_class=IngestRunFilter,
        description="Get all ingest runs",
    )

    def resolve_all_ingest_runs(self, info, **kwargs):
        """
        Return all ingest runs
        """
        user = info.context.user

        if not user.has_perm("ingests.list_all_ingestrun"):
            raise GraphQLError("Not allowed")

        return IngestRun.objects.all()
