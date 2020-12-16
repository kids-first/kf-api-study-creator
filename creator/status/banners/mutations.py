import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id

from creator.status.banners.nodes import BannerNode
from creator.status.banners.models import Banner


class BannerInput(graphene.InputObjectType):
    """ Parameters used when creating a new banner """

    start_date = graphene.DateTime(
        required=False, description="When to start displaying the banner"
    )
    end_date = graphene.DateTime(
        required=False, description="When to stop displaying the banner"
    )
    enabled = graphene.Boolean(
        required=False, description="Whether to display the banner or not"
    )
    severity = graphene.String(
        required=False, description="Severity of the message"
    )
    message = graphene.String(
        description="The message content for the banner"
    )
    url = graphene.String(
        description="A URL that may be included in the Banner's message as an "
        "HTML <a> element, pointing to additional information about message",
        required=False
    )
    url_label = graphene.String(
        description="A text label meant to be used as a part of the <a> "
        "element containing the Banner url",
        required=False
    )


class CreateBannerMutation(graphene.Mutation):
    """ Creates a new banner """

    class Arguments:
        input = BannerInput(
            required=True, description="Attributes for the new banner"
        )

    banner = graphene.Field(BannerNode)

    def mutate(self, info, input):
        """
        Creates a new banner.
        """
        user = info.context.user
        if not user.has_perm("status.add_banner"):
            raise GraphQLError("Not allowed")

        banner = Banner(**{k: input[k] for k in input})
        banner.creator = user
        banner.save()

        return CreateBannerMutation(banner=banner)


class UpdateBannerMutation(graphene.Mutation):
    """ Update an existing banner """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the banner to update"
        )
        input = BannerInput(
            required=True, description="Attributes for the banner"
        )

    banner = graphene.Field(BannerNode)

    def mutate(self, info, id, input):
        """
        Updates an existing banner
        """
        user = info.context.user
        if not user.has_perm("status.change_banner"):
            raise GraphQLError("Not allowed")

        model, node_id = from_global_id(id)

        try:
            banner = Banner.objects.get(id=node_id)
        except Banner.DoesNotExist:
            raise GraphQLError("Banner was not found")

        for attr in [
            "message", "start_date", "end_date", "enabled", "severity",
            "url", "url_label"
        ]:
            if attr in input:
                setattr(banner, attr, input[attr])

        banner.save()

        return UpdateBannerMutation(banner=banner)


class Mutation:
    """ Mutations for banner """

    create_banner = CreateBannerMutation.Field(
        description="Create a new banner."
    )
    update_banner = UpdateBannerMutation.Field(
        description="Update a given banner"
    )
