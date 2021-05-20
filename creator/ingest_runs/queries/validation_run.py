from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter

from creator.ingest_runs.nodes import ValidationRunNode
from creator.ingest_runs.models import ValidationRun
from creator.ingest_runs.common.model import State


class ValidationRunFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))

    class Meta:
        model = ValidationRun
        fields = {"success": ["exact"]}


class ValidationRunFilterLatest(FilterSet):
    order_by = OrderingFilter(fields=("modified_at",))

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
    last_modified_validation_run = DjangoFilterConnectionField(
        ValidationRunNode,
        filterset_class=ValidationRunFilterLatest,
        description="Get the last modifed validation_run",
    )

    def resolve_all_validation_runs(self, info, **kwargs):
        """
        Return all validation_runs
        """
        user = info.context.user

        if not user.has_perm("ingest_runs.list_all_validationrun"):
            raise GraphQLError("Not allowed")

        return ValidationRun.objects.all()
    
    def resolve_last_modified_validation_run(self, info, **kwargs):
        """
        Return the last modified validation_run
        """
        user = info.context.user
        
        if not user.has_perm("ingest_runs.list_all_validationrun"):
            raise GraphQLError("Not allowed")
        terminal_states = [
            State.CANCELED,
            State.COMPLETED,
            State.FAILED,
        ]
        return ValidationRun.objects.exclude(state__in=terminal_states).latest(
            "modified_at"
        )
