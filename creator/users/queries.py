import graphene
import django_filters
from graphene import relay
from graphql import GraphQLError
from graphene_django.filter import (
    DjangoFilterConnectionField,
    GlobalIDFilter,
)
from django_filters import OrderingFilter

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    organization = GlobalIDFilter(field_name="organizations")

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


class GroupFilter(django_filters.FilterSet):
    name_contains = django_filters.CharFilter(
        field_name="name", lookup_expr="contains"
    )

    class Meta:
        model = Group
        fields = {"name": ["exact"]}


class PermissionFilter(django_filters.FilterSet):
    name_contains = django_filters.CharFilter(
        field_name="name", lookup_expr="contains"
    )

    class Meta:
        model = Permission
        fields = {"name": ["exact"], "codename": ["exact"]}


class Query(object):
    all_users = DjangoFilterConnectionField(
        "creator.users.schema.UserNode",
        filterset_class=UserFilter,
    )
    my_profile = graphene.Field("creator.users.schema.UserNode")
    group = relay.Node.Field(
        "creator.users.schema.GroupNode",
        description="Get a group",
    )
    all_groups = DjangoFilterConnectionField(
        "creator.users.schema.GroupNode",
        filterset_class=GroupFilter,
        description="List all groups",
    )
    permission = relay.Node.Field(
        "creator.users.schema.PermissionNode",
        description="Get a permission",
    )
    all_permissions = DjangoFilterConnectionField(
        "creator.users.schema.PermissionNode",
        filterset_class=PermissionFilter,
        description="List all permissions",
    )

    def resolve_all_users(self, info, **kwargs):
        """
        If user is USER, only return that user
        If user is ADMIN, return all users
        If user is unauthed, return no users
        """
        user = info.context.user
        if user is None or not user.is_authenticated:
            return User.objects.none()

        # Only return the current user if there are insufficient permissions
        if user.is_authenticated and not user.has_perm(
            "creator.list_all_user"
        ):
            return User.objects.filter(sub=user.sub).all()

        return User.objects.all()

    def resolve_my_profile(self, info, **kwargs):
        """
        Return the user that is making the request if they are valid,
        otherwise, return nothing
        """
        user = info.context.user

        # Unauthed and service users do not have profiles
        if not user.is_authenticated or user is None or user.username is None:
            raise GraphQLError("not authenticated as a user with a profile")

        return user

    def resolve_all_groups(self, info, **kwargs):
        user = info.context.user
        if not user.has_perm("auth.view_group"):
            raise GraphQLError("Not allowed")

        return Group.objects.all()

    def resolve_all_permissions(self, info, **kwargs):
        user = info.context.user
        if not user.has_perm("auth.view_permission"):
            raise GraphQLError("Not allowed")

        return Permission.objects.all()
