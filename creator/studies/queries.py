import logging
import graphene
from graphql import GraphQLError
from graphene_django.filter import DjangoFilterConnectionField

from creator.studies.nodes import StudyNode
from creator.studies.models import Study

logger = logging.getLogger(__name__)


class Query:
    study = graphene.relay.Node.Field(StudyNode, description="Get a study")
    study_by_kf_id = graphene.Field(
        StudyNode,
        kf_id=graphene.String(required=True),
        description="Get a study by its kf_id",
    )
    all_studies = DjangoFilterConnectionField(
        StudyNode, description="List all studies"
    )

    def resolve_study_by_kf_id(self, info, kf_id):
        return StudyNode.get_node(info, kf_id)

    def resolve_all_studies(self, info, **kwargs):
        """
        If user is USER, only return the studies which the user belongs to
        If user is ADMIN, return all studies
        If user is unauthed, return no studies
        """
        user = info.context.user

        if user.has_perm("studies.view_study"):
            return Study.objects.filter(deleted=False)

        if user.has_perm("studies.view_my_study"):
            return user.studies.filter(deleted=False).all(), info

        raise GraphQLError("Not allowed")
