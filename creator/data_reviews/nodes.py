from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.data_reviews.models import DataReview


class DataReviewNode(DjangoObjectType):
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

        if not (user.has_perm("data_reviews.view_datareview")):
            raise GraphQLError("Not allowed")

        try:
            data_review = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("DataReviews was not found")

        return data_review
