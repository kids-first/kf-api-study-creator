from graphene import relay
from graphene_django.filter import (
    DjangoFilterConnectionField
)
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter, CharFilter

from creator.storage_analyses.nodes import StorageAnalysisNode, FileAuditNode
from creator.storage_analyses.models import (
    StorageAnalysis,
    FileAudit,
    ResultEnum
)


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
    all_cloud_inventory_files = DjangoFilterConnectionField(
        FileAuditNode,
        filterset_class=FileAuditFilter,
        description="Get all files in the cloud storage inventory",
    )
    all_upload_manifest_files = DjangoFilterConnectionField(
        FileAuditNode,
        filterset_class=FileAuditFilter,
        description="Get all files in the cloud upload manifests",
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

        if user.has_perm("storage_analyses.list_all_storageanalysis"):
            return StorageAnalysis.objects.all()
        else:
            return StorageAnalysis.objects.filter(
                study__in=user.studies.all()
            ).all()

    def resolve_all_file_audits(self, info, **kwargs):
        """
        Return all file audits
        """
        user = info.context.user

        if user.has_perm("storage_analyses.list_all_storageanalysis"):
            return FileAudit.objects.all()
        else:
            return FileAudit.objects.filter(
                storage_analysis__study__in=user.studies.all()
            ).all()

    def resolve_all_cloud_inventory_files(self, info, **kwargs):
        """
        Return all files in inventoried in cloud storage
        """
        user = info.context.user

        if user.has_perm("storage_analyses.list_all_storageanalysis"):
            query = FileAudit.objects
        else:
            query = FileAudit.objects.filter(
                storage_analysis__study__in=user.studies.all()
            )

        # Returns files found in both cloud storage inventory and upload
        # manifests AND files found only in cloud storage inventory. This is
        # the equivalent of returning a table of files in cloud storage
        # inventory
        return query.filter(result__in=[
            ResultEnum.matched.value,
            ResultEnum.moved.value,
            ResultEnum.unexpected.value,
        ]).all()

    def resolve_all_upload_manifest_files(self, info, **kwargs):
        """
        Return all files uploaded to cloud storage
        """
        user = info.context.user

        if user.has_perm("storage_analyses.list_all_storageanalysis"):
            query = FileAudit.objects
        else:
            query = FileAudit.objects.filter(
                storage_analysis__study__in=user.studies.all()
            )

        # Returns files found in both cloud storage inventory and upload
        # manifests AND files found only in the upload manifests. This is the
        # equivalent of returning an aggregate table of files from the upload
        # manifests
        return query.filter(result__in=[
            ResultEnum.matched.value,
            ResultEnum.moved.value,
            ResultEnum.missing.value,
        ]).all()
