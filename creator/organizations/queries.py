import graphene
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, OrderingFilter
from graphql import GraphQLError

from creator.organizations.models import Organization
from creator.organizations.nodes import OrganizationNode


class OrganizationFilter(FilterSet):
    order_by = OrderingFilter(fields=("name", "created_on"))

    class Meta:
        model = Organization
        fields = ["name"]


class Query:
    organization = graphene.relay.Node.Field(
        OrganizationNode, description="Get a single organization"
    )
    all_organizations = DjangoFilterConnectionField(
        OrganizationNode,
        filterset_class=OrganizationFilter,
        description="Get all organizations",
    )

    def resolve_all_organizations(self, info, **kwargs):
        """
        Return all organizations of the user has list_all_organization.
        Return only organizations the user is a member of if they have
            view_my_study
        """
        user = info.context.user

        if user.has_perm("organizations.list_all_organization"):
            return Organization.objects.all()

        if user.has_perm("organizations.view_my_organization"):
            return user.organizations.all()

        raise GraphQLError("Not allowed")
