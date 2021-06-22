import graphene
import django_filters
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import OrderingFilter
from graphql import GraphQLError

from creator.referral_tokens.models import ReferralToken
from creator.users.schema import UserNode

from creator.referral_tokens.mutations import Mutation


class ReferralTokenNode(DjangoObjectType):
    is_valid = graphene.Boolean(source="is_valid")

    class Meta:
        model = ReferralToken
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, uuid):
        """
        Only return if the user is allowed to view referral token
        """
        user = info.context.user

        if not (user.has_perm("referral_tokens.view_referraltoken")):
            raise GraphQLError("Not allowed")

        try:
            return cls._meta.model.objects.get(uuid=uuid)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Referral token not found")


class ReferralTokenFilter(django_filters.FilterSet):
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lt"
    )
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gt"
    )
    email_contains = django_filters.CharFilter(
        field_name="email", lookup_expr="contains"
    )

    class Meta:
        model = ReferralToken
        fields = {
            "email": ["exact"],
            "claimed": ["exact"],
            "studies": ["exact"],
            "groups": ["exact"],
            "organization": ["exact"],
        }

    order_by = OrderingFilter(fields=("created_at",))


class Query(object):
    referral_token = relay.Node.Field(
        ReferralTokenNode, description="Get a single referral token"
    )
    all_referral_tokens = DjangoFilterConnectionField(
        ReferralTokenNode,
        filterset_class=ReferralTokenFilter,
        description="Get all referral tokens",
    )

    def resolve_all_referral_tokens(self, info, **kwargs):
        """
        Return all referral tokens if user has list_all_referraltoken
        Return not allowed otherwise
        """
        user = info.context.user

        if not (user.has_perm("referral_tokens.list_all_referraltoken")):
            raise GraphQLError("Not allowed")

        if user.has_perm("referral_tokens.list_all_referraltoken"):
            return ReferralToken.objects.all()

        return ReferralToken.objects.none()
