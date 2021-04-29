import graphene
from graphene_django import DjangoObjectType

from creator.organizations.models import Organization


class OrganizationNode(DjangoObjectType):
    class Meta:
        model = Organization
        interfaces = (graphene.relay.Node,)

    @classmethod
    def get_node(cls, info, pk):
        """
        Only return node if user may see their organizations and belongs to the
        organization or if they may see all organizations.
        """
        try:
            organization = cls._meta.model.objects.get(pk=pk)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Organization was not found")

        user = info.context.user
        if user.has_perm("organizations.view_organization") or (
            user.has_perm("organizations.view_my_organization")
            and user.organizations.filter(pk=organization.pk).exists()
        ):
            return organization
        else:
            raise GraphQLError("Not allowed")
