from django.conf import settings
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphql import GraphQLError

from ..models import Version


class VersionNode(DjangoObjectType):
    class Meta:
        model = Version
        interfaces = (relay.Node,)

    matches_template = graphene.Boolean(source="matches_template")
    download_url = graphene.String()
    valid_types = graphene.List("creator.files.nodes.file.FileType")

    def resolve_download_url(self, info):
        path = self.path
        if path is None:
            return None
        protocol = "http" if settings.DEVELOP else "https"
        return f"{protocol}://{info.context.get_host()}{self.path}"

    @classmethod
    def get_node(cls, info, kf_id):
        """
        Only return node if user is an admin or is in the study group
        """
        try:
            obj = cls._meta.model.objects.get(kf_id=kf_id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Version was not found")

        user = info.context.user
        if user.has_perm("files.view_version") or (
            user.has_perm("files.view_my_version")
            and user.studies.filter(kf_id=obj.root_file.study.kf_id).exists()
        ):
            return obj

        raise GraphQLError("Not allowed")
