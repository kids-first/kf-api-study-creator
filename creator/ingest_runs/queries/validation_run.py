from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter

from creator.ingest_runs.nodes import ValidationRunNode
from creator.ingest_runs.models import ValidationRun


class ValidationRunFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))

    class Meta:
        model = ValidationRun
        fields = {"success": ["exact"]}


class Query(object):
    validation_run = relay.Node.Field(
        ValidationRunNode, description="Get a single validation_run"
    )
    all_validation_runs = DjangoFilterConnectionField(
        ValidationRunNode,
        filterset_class=ValidationRunFilter,
        description="Get all validation_runs",
    )

    def resolve_all_validation_runs(self, info, **kwargs):
        """
        Return all validation_runs
        """
        user = info.context.user

        if not user.has_perm("ingest_runs.list_all_validationrun"):
            raise GraphQLError("Not allowed")

        return ValidationRun.objects.all()
