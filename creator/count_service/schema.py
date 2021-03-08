import django_filters
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, OrderingFilter
from graphql import GraphQLError

from creator.count_service.models import CountTask, StudySummary


class StudySummaryFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))

    class Meta:
        model = StudySummary
        fields = ["study"]


class StudySummaryNode(DjangoObjectType):
    class Meta:
        model = StudySummary
        interfaces = (graphene.relay.Node,)

    @classmethod
    def get_node(cls, info, pk):
        """
        Only return node if user is admin
        """
        user = info.context.user

        if not user.has_perm("jobs.view_studysummary"):
            return StudySummaryNode.objects.none()

        return StudySummaryNode.objects.get(pk=pk)


class Query(object):
    study_summary = relay.Node.Field(
        StudySummaryNode, description="Get a single study summary"
    )
    all_study_summaries = DjangoFilterConnectionField(
        StudySummaryNode,
        filterset_class=StudySummaryFilter,
        description="Get all study summaries",
    )

    def resolve_all_study_summaries(self, info, **kwargs):
        """
        Return all study summaries
        """
        user = info.context.user
        if not user.has_perm("count_service.list_all_studysummary"):
            raise GraphQLError("Not allowed")

        return StudySummary.objects.all()
