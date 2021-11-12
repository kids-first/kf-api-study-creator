from django.conf import settings
import graphene
from graphql import GraphQLError
from creator.data_templates.nodes.template_version import TemplateVersionNode

class InventoryStats(graphene.ObjectType):
    """
    Analysis of files in the storage inventory
    """
    total_buckets = graphene.Dict()
    total_count = graphene.Dict()
    total_size = graphene.Dict()

class StorageAnalysisStats(graphene.ObjectType):
    """
    Encapsulates the results of a study's cloud storage analysis
    """
    # upload = UploadStats(
    #     description="Analysis of files in the file upload manifests"
    # )
    inventory = InventoryStats(
        description="Analysis of files in the storage inventory"
    )
    # audit = AuditStats(
    #     description="Comparison of files uploaded with files in storage "
    #     "inventory"
    # )
