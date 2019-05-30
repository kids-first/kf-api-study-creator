import graphene
import django_filters
from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import OrderingFilter

from graphql import GraphQLError
from django.contrib.auth import get_user_model

User = get_user_model()


class UserNode(DjangoObjectType):
    class Meta:
        model = User
        interfaces = (relay.Node,)
        only_fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "last_login",
            "date_joined",
        ]

    @classmethod
    def get_node(cls, info, sub):
        """
        Only return node if user is an admin or is self
        """
        try:
            obj = cls._meta.model.objects.get(sub=sub)
        except cls._meta.model.DoesNotExist:
            return None

        user = info.context.user

        if not user.is_authenticated:
            return None

        if user.is_admin:
            return obj

        if obj.sub == user.sub:
            return obj

        return None


class UserFilter(django_filters.FilterSet):
    class Meta:
        model = User
        fields = {
            "email": ["exact", "contains"],
            "username": ["exact"],
            "first_name": ["exact"],
            "last_name": ["exact"],
            "last_login": ["gt", "lt"],
            "date_joined": ["gt", "lt"],
        }

    order_by = OrderingFilter(fields=("date_joined",))


class Query(object):
    all_users = DjangoFilterConnectionField(
        UserNode, filterset_class=UserFilter
    )

    def resolve_all_users(self, info, **kwargs):
        """
        If user is USER, only return that user
        If user is ADMIN, return all users
        If user is unauthed, return no users
        """
        user = info.context.user

        if not user.is_authenticated or user is None:
            return User.objects.none()

        if user.is_admin:
            return User.objects.all()

        return [user]
