import graphene
import django_filters
from graphene import relay, ObjectType, Field, List, String
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import OrderingFilter

from graphql import GraphQLError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from creator.studies.models import Study
from creator.studies.schema import StudyNode

User = get_user_model()


class UserNode(DjangoObjectType):
    roles = List(String, description="Roles that the user has")

    def resolve_roles(self, info):
        return self.ego_roles

    groups = List(String, description="Groups that the user belongs to")

    def resolve_groups(self, info):
        return self.ego_groups

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
            "picture",
            "study_subscriptions",
            "slack_notify",
            "slack_member_id",
            "email_notify",
            "studies"
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


class GroupNode(DjangoObjectType):
    class Meta:
        model = Group
        interfaces = (relay.Node,)

    @classmethod
    def get_node(cls, info, id):
        """
        Only return node if user is an admin or is self
        """
        user = info.context.user
        if not user.has_perm("auth.view_group"):
            raise GraphQLError("Not allowed")

        try:
            obj = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Group not found")

        return obj


class PermissionNode(DjangoObjectType):
    class Meta:
        model = Permission
        interfaces = (relay.Node,)

    @classmethod
    def get_node(cls, info, id):
        user = info.context.user
        if not user.has_perm("auth.view_permission"):
            raise GraphQLError("Not allowed")

        try:
            obj = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Permission not found")

        return obj


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


class MyProfileMutation(graphene.Mutation):
    """
    Updates user's profile
    Only modifies the request's authenticated user's profile.
    We can only change fields that originate in our data model as the other
    fields come from our authentication services.
    """

    class Arguments:
        slack_notify = graphene.Boolean()
        slack_member_id = graphene.String()
        email_notify = graphene.Boolean()

    user = graphene.Field(UserNode)

    def mutate(self, info, **kwargs):
        """
        Updates a user's profile.
        Only applies to the request's current user
        """
        user = info.context.user
        if not user.is_authenticated or user is None or user.email == "":
            raise GraphQLError("Not authenticated to mutate profile")

        if "slack_notify" in kwargs:
            user.slack_notify = kwargs.get("slack_notify")
        if "slack_member_id" in kwargs:
            user.slack_member_id = kwargs.get("slack_member_id")
        if "email_notify" in kwargs:
            user.email_notify = kwargs.get("email_notify")
        user.save()

        return MyProfileMutation(user=user)


class SubscribeToMutation(graphene.Mutation):
    """
    Subscribe a user to a study
    admin - may subscribe to any study
    service - may not subscribe to studies
    user - may only subscribe to studies which they are in the group of
    unauthed - may not subscribe to studies
    """

    class Arguments:
        study_id = graphene.String(required=True)

    success = graphene.Boolean()
    user = graphene.Field(UserNode)

    def mutate(self, info, study_id, **kwargs):
        """
        Adds a study to the user's study subscriptions
        """
        user = info.context.user
        if user is None or not user.is_authenticated:
            raise GraphQLError("Not authenticated to subscribe")

        try:
            study = Study.objects.get(kf_id=study_id)
        except Study.DoesNotExist:
            raise GraphQLError("Study does not exist.")

        if study_id not in user.ego_groups and "ADMIN" not in user.ego_roles:
            raise GraphQLError("Not authenticated to subscribe")

        # Add the study to the users subscriptions
        user.study_subscriptions.add(study)

        return SubscribeToMutation(success=True, user=user)


class UnsubscribeFromMutation(graphene.Mutation):
    """
    Unsubscribes a user from a study
    """

    class Arguments:
        study_id = graphene.String(required=True)

    success = graphene.Boolean()
    user = graphene.Field(UserNode)

    def mutate(self, info, study_id, **kwargs):
        """
        Removes a study from the user's study subscriptions
        """
        user = info.context.user
        if user is None or not user.is_authenticated:
            raise GraphQLError("Not authenticated to unsubscribe")

        try:
            study = Study.objects.get(kf_id=study_id)
        except Study.DoesNotExist:
            raise GraphQLError("Study does not exist.")

        # Remove the study to the users subscriptions
        user.study_subscriptions.remove(study)

        return SubscribeToMutation(success=True, user=user)


class Query(object):
    all_users = DjangoFilterConnectionField(
        UserNode, filterset_class=UserFilter
    )
    my_profile = Field(UserNode)
    group = relay.Node.Field(GroupNode, description="Get a group")
    all_groups = DjangoFilterConnectionField(
        GroupNode, filterset_class=GroupFilter, description="List all groups"
    )
    permission = relay.Node.Field(
        PermissionNode, description="Get a permission"
    )
    all_permissions = DjangoFilterConnectionField(
        PermissionNode,
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

        if not user.is_authenticated or user is None:
            return User.objects.none()

        if user.is_admin:
            return User.objects.all()

        return [user]

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
