import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id

from django.conf import settings
from creator.data_reviews.nodes import DataReviewNode
from creator.data_reviews.models import DataReview


class CreateDataReviewInput(graphene.InputObjectType):
    """ Parameters used when creating a new data_review """

    name = graphene.String(description="The name of the data_review")


class UpdateDataReviewInput(graphene.InputObjectType):
    """ Parameters used when updating an existing data_review """

    name = graphene.String(description="The name of the data_review")


class CreateDataReviewMutation(graphene.Mutation):
    """ Creates a new data_review """

    class Arguments:
        input = CreateDataReviewInput(
            required=True, description="Attributes for the new data_review"
        )

    data_review = graphene.Field(DataReviewNode)

    def mutate(self, info, input):
        """
        Creates a new data_review.
        """
        user = info.context.user
        if not user.has_perm("data_reviews.add_datareview"):
            raise GraphQLError("Not allowed")

        data_review = DataReview()
        return CreateDataReviewMutation(data_review=data_review)


class UpdateDataReviewMutation(graphene.Mutation):
    """ Update an existing data_review """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the data_review to update"
        )
        input = UpdateDataReviewInput(
            required=True, description="Attributes for the data_review"
        )

    data_review = graphene.Field(DataReviewNode)

    def mutate(self, info, id, input):
        """
        Updates an existing data_review
        """
        user = info.context.user
        if not user.has_perm("data_reviews.change_datareview"):
            raise GraphQLError("Not allowed")

        model, node_id = from_global_id(id)

        try:
            data_review = DataReview.objects.get(id=node_id)
        except DataReview.DoesNotExist:
            raise GraphQLError("DataReview was not found")

        return UpdateDataReviewMutation(data_review=data_review)


class Mutation:
    """ Mutations for data_reviews """

    create_data_review = CreateDataReviewMutation.Field(
        description="Create a new data_review."
    )
    update_data_review = UpdateDataReviewMutation.Field(
        description="Update a given data_review"
    )
