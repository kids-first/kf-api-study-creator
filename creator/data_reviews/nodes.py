from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from creator.events.schema import EventNode, EventFilter

from creator.data_reviews.models import DataReview


class DataReviewNode(DjangoObjectType):
    events = DjangoFilterConnectionField(
        EventNode, filterset_class=EventFilter, description="List all events"
    )

    class Meta:
        model = DataReview
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        try:
            data_review = cls._meta.model.objects.get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("DataReviews was not found")

        if not (
            user.has_perm("data_reviews.add_datareview")
            or (
                user.has_perm("data_reviews.add_my_study_datareview")
                and user.studies.filter(kf_id=data_review.study.kf_id).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        return data_review
