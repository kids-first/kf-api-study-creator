from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter

from creator.ingest_runs.nodes import IngestRunNode
from creator.ingest_runs.models import IngestRun


class IngestRunFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))

    class Meta:
        model = IngestRun
        fields = {"name": ["exact", "icontains"]}


class Query(object):
    ingest_run = relay.Node.Field(
        IngestRunNode, description="Get a single ingest_run"
    )
    all_ingest_runs = DjangoFilterConnectionField(
        IngestRunNode,
        filterset_class=IngestRunFilter,
        description="Get all ingest_runs",
    )

    def resolve_all_ingest_runs(self, info, **kwargs):
        """
        Return all ingest_runs
        """
        user = info.context.user

        if not user.has_perm("ingest_runs.list_all_ingestrun"):
            raise GraphQLError("Not allowed")

        return IngestRun.objects.all()
