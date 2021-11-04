from graphene import relay
from graphene_django.filter import (
    DjangoFilterConnectionField
)
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter, CharFilter

from creator.storage_analyses.nodes import StorageAnalysisNode, FileAuditNode
from creator.storage_analyses.models import StorageAnalysis, FileAudit


class StorageAnalysisFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_at",))
    study_kf_id = CharFilter(field_name="study__kf_id", lookup_expr="exact")

    class Meta:
        model = StorageAnalysis
        fields = []


class FileAuditFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_at",))

    class Meta:
        model = FileAudit
        fields = ["storage_analysis", "result"]


class Query(object):
    storage_analysis = relay.Node.Field(
        StorageAnalysisNode, description="Get a single storage_analysis"
    )
    file_audit = relay.Node.Field(
        FileAuditNode, description="Get a single file audit"
    )
    all_file_audits = DjangoFilterConnectionField(
        FileAuditNode,
        filterset_class=FileAuditFilter,
        description="Get all file_audits",
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

        return StorageAnalysis.objects.filter(
            study__in=user.studies.all()
        ).all()

    def resolve_all_file_audits(self, info, **kwargs):
        """
        Return all file audits
        """
        user = info.context.user

        if not user.has_perm("storage_analyses.list_all_storageanalysis"):
            raise GraphQLError("Not allowed")

        return FileAudit.objects.filter(
            storage_analysis__study__in=user.studies.all()
        ).all()
