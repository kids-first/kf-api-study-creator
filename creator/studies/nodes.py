import graphene
from graphql import GraphQLError
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from creator.events.schema import EventNode, EventFilter
from creator.files.schema.file import FileNode, FileFilter
from creator.releases.nodes import ReleaseNode
from creator.releases.queries import ReleaseFilter
from creator.studies.models import (
    Study,
    SEQ_STATUS_CHOICES,
    ING_STATUS_CHOICES,
    PHE_STATUS_CHOICES,
)


class StudyNode(DjangoObjectType):
    """ A study in Kids First """

    events = DjangoFilterConnectionField(
        EventNode, filterset_class=EventFilter, description="List all events"
    )

    files = DjangoFilterConnectionField(
        FileNode, filterset_class=FileFilter, description="List all files"
    )

    releases = DjangoFilterConnectionField(
        ReleaseNode,
        filterset_class=ReleaseFilter,
        description="List all releases for the study",
    )

    class Meta:
        model = Study
        filter_fields = ["name", "investigator_name"]
        exclude = ["user_set"]
        interfaces = (graphene.relay.Node,)

    @classmethod
    def get_node(cls, info, kf_id):
        """
        Only return node if user is an admin or is in the study group
        """
        try:
            study = cls._meta.model.objects.get(kf_id=kf_id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Study was not found")

        user = info.context.user
        if user.has_perm("studies.view_study") or (
            user.has_perm("studies.view_my_study")
            and user.studies.filter(kf_id=study.kf_id).exists()
        ):
            return study
        else:
            raise GraphQLError("Not allowed")


SequencingStatusType = graphene.Enum(
    "SequencingStatusType",
    [
        (status[0], status[0].replace("-", "_"))
        for status in SEQ_STATUS_CHOICES
    ],
)

IngestionStatusType = graphene.Enum(
    "IngestionStatusType",
    [
        (status[0], status[0].replace("-", "_"))
        for status in ING_STATUS_CHOICES
    ],
)

PhenotypeStatusType = graphene.Enum(
    "PhenotypeStatusType",
    [
        (status[0], status[0].replace("-", "_"))
        for status in PHE_STATUS_CHOICES
    ],
)
