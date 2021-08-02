import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, OrderingFilter
from graphql import GraphQLError

from creator.organizations.models import Organization
from creator.users.queries import UserFilter


class OrganizationFilter(FilterSet):
    order_by = OrderingFilter(fields=("name", "created_on"))

    class Meta:
        model = Organization
        fields = ["name"]


class OrganizationNode(DjangoObjectType):
    users = DjangoFilterConnectionField(
        "creator.users.schema.UserNode",
        filterset_class=UserFilter,
        description="List all users in an organization",
    )

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


class Query:
    organization = graphene.relay.Node.Field(
        OrganizationNode,
        description="Get a single organization",
    )
    all_organizations = DjangoFilterConnectionField(
        OrganizationNode,
        filterset_class=OrganizationFilter,
        description="Get all organizations",
    )

    def resolve_all_organizations(self, info, **kwargs):
        """
        Return all organizations if the user has list_all_organization.
        Return only organizations the user is a member of if they have
            view_my_study
        """
        user = info.context.user

        if user.has_perm("organizations.list_all_organization"):
            return Organization.objects.all()

        if user.has_perm("organizations.view_my_organization"):
            return user.organizations.all()

        raise GraphQLError("Not allowed")
