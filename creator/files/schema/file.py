import graphene
import django_filters
from graphene import relay, Field, String
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from .version import VersionNode, VersionFilter

from creator.files.mutations.file import Mutation as FileMutation
from creator.files.mutations.version import Mutation as VersionMutation


from ..models import File, Version
from creator.studies.models import Study
from creator.files.nodes.file import FileNode


class FileFilter(django_filters.FilterSet):
    tag = django_filters.CharFilter(field_name="tags", lookup_expr="icontains")

    class Meta:
        model = File
        fields = ["name", "study__kf_id", "file_type"]


class Query:
    file = relay.Node.Field(FileNode, description="Get a file")
    file_by_kf_id = Field(
        FileNode,
        kf_id=String(required=True),
        description="Get a file by its kf_id",
    )
    all_files = DjangoFilterConnectionField(
        FileNode, filterset_class=FileFilter, description="List all files"
    )

    def resolve_file_by_kf_id(self, info, kf_id):
        return FileNode.get_node(info, kf_id)

    def resolve_all_files(self, info, **kwargs):
        """
        If user is USER, only return the files from the studies
        which the user belongs to
        If user is ADMIN, return all files
        If user is unauthed, return no files
        """
        user = info.context.user
        if user.has_perm("files.list_all_file"):
            return File.objects.all()

        # Only return files that the user is a member of
        if user.has_perm("files.view_my_file"):
            return File.objects.filter(study__in=user.studies.all()).all()

        raise GraphQLError("Not allowed")
