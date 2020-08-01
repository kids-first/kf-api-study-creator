import django_filters
from graphql_relay import from_global_id
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError

from creator.analyses.models import Analysis
from creator.analyses.mutations import Mutation


class AnalysisNode(DjangoObjectType):
    class Meta:
        model = Analysis
        interfaces = (relay.Node,)

    @classmethod
    def get_node(cls, info, id):
        """
        Only return if the user is allowed to view analyses
        """
        user = info.context.user

        if not (
            user.has_perm("analyses.view_analysis")
            or user.has_perm("analyses.view_my_study_analysis")
        ):
            raise GraphQLError("Not allowed")

        try:
            analysis = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Analysis does not exist")

        # If user only has view_my_study_analysis, make sure the analysis
        # belongs to one of their studies
        if user.has_perm("analyses.view_analysis") or (
            user.has_perm("analyses.view_my_study_analysis")
            and analysis.study
            and user.studies.filter(kf_id=analysis.study.kf_id).exists()
        ):
            return analysis

        raise GraphQLError("Not allowed")


class AnalysisFilter(django_filters.FilterSet):
    file_kf_id = django_filters.CharFilter(
        field_name="root_file__kf_id", lookup_expr="exact"
    )

    class Meta:
        model = Analysis
        fields = ["creator", "known_format"]

    order_by = django_filters.OrderingFilter(fields=("created_at",))


class Query(object):
    analysis = relay.Node.Field(
        AnalysisNode, description="Get a single analysis"
    )
    all_analyses = DjangoFilterConnectionField(
        AnalysisNode,
        filterset_class=AnalysisFilter,
        description="Get all analyses",
    )

    def resolve_all_analyses(self, info, **kwargs):
        """
        Return all analyses if user has view_analysis
        Return only analyses in user's studies if user has view_my_analysis
        Return not allowed otherwise
        """
        user = info.context.user

        if not (
            user.has_perm("analyses.list_all_analysis")
            or user.has_perm("analyses.view_my_study_analysis")
        ):
            raise GraphQLError("Not allowed")

        if user.has_perm("analyses.list_all_analysis"):
            return Analysis.objects.all()

        if user.has_perm("analyses.view_my_study_analysis"):
            return Analysis.objects.filter(
                root_file__study__in=user.studies.all()
            ).all()

        raise GraphQLError("Not allowed")
