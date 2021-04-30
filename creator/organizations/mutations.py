import graphene
from graphql import GraphQLError

from creator.organizations.models import Organization
from creator.organizations.nodes import OrganizationNode


class CreateOrganizationInput(graphene.InputObjectType):
    """ Schema for creating a new study """

    name = graphene.String(
        required=True, description="The name of the organization"
    )
    description = graphene.String(
        required=False, description="The description of the organization"
    )
    website = graphene.String(
        required=False, description="The url of the organization's website"
    )
    email = graphene.String(
        required=False, description="The email address of the organization"
    )
    image = graphene.String(
        required=False,
        description="The url of the display image for the organization",
    )


class CreateOrganizationMutation(graphene.Mutation):
    """ Mutation to create a new organization """

    class Arguments:
        """ Arguments for creating a new organization """

        input = CreateOrganizationInput(
            required=True, description="Attributes for the new organization"
        )

    organization = graphene.Field(OrganizationNode)

    def mutate(self, info, input):
        """
        Create a new organization and add the requesting user to it.
        """
        user = info.context.user
        if not user.has_perm("organizations.add_organization"):
            raise GraphQLError("Not allowed")

        organization = Organization(**input)
        organization.clean_fields()
        organization.save()
        organization.members.add(user)
        return CreateOrganizationMutation(organization=organization)


class Mutation:
    create_organization = CreateOrganizationMutation.Field(
        description="Create a new organization"
    )
