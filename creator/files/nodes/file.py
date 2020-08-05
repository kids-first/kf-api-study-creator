import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError

from ..models import File, Version
from creator.files.nodes.version import VersionNode
from creator.files.schema.version import VersionFilter


class FileNode(DjangoObjectType):
    class Meta:
        model = File
        interfaces = (relay.Node,)

    versions = DjangoFilterConnectionField(
        VersionNode, filterset_class=VersionFilter
    )

    download_url = graphene.String()

    def resolve_download_url(self, info):
        return f"https://{info.context.get_host()}{self.path}"

    @classmethod
    def get_node(cls, info, kf_id):
        """
        Only return node if user is an admin or is in the study group
        """

        try:
            file = cls._meta.model.objects.get(kf_id=kf_id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("File was not found")

        user = info.context.user
        if user.has_perm("files.view_file") or (
            user.has_perm("files.view_my_file")
            and user.studies.filter(kf_id=file.study.kf_id).exists()
        ):
            return file

        raise GraphQLError("Not allowed")
