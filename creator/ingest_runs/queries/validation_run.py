from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField, ListFilter
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter

from creator.ingest_runs.nodes import ValidationRunNode
from creator.ingest_runs.models import ValidationRun


class ValidationRunFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on", "modified_at"))

    class Meta:
        model = ValidationRun
        fields = {
            "success": ["exact"],
            "data_review": ["exact"],
            "state": ["exact", "icontains"],
        }

    state_in = ListFilter(field_name="state", lookup_expr="in")


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
