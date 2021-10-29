from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter, CharFilter

from creator.storage_analyses.nodes import StorageAnalysisNode
from creator.storage_analyses.models import StorageAnalysis


class StorageAnalysisFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))
    study_kf_id = CharFilter(field_name="study__kf_id", lookup_expr="exact")

    class Meta:
        model = StorageAnalysis
        fields = []


class Query(object):
    storage_analysis = relay.Node.Field(
        StorageAnalysisNode, description="Get a single storage_analysis"
    )
    all_storage_analyses = DjangoFilterConnectionField(
        StorageAnalysisNode,
        filterset_class=StorageAnalysisFilter,
        description="Get all storage_analyses",
    )

    def resolve_all_storage_analyses(self, info, **kwargs):
        """
        Return all storage_analyses
        """
        user = info.context.user

        if not user.has_perm("storage_analyses.list_all_storageanalysis"):
            raise GraphQLError("Not allowed")

        return StorageAnalysis.objects.all()
