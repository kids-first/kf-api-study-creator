import graphene
import django_filters
from graphene import (
    relay,
    Connection,
    ObjectType,
    Field,
    List,
    String,
    DateTime,
)
from graphql_relay import from_global_id
from graphene_django import DjangoObjectType
from graphene_django.utils import get_model_fields
from graphene_django.converter import convert_django_field_with_choices
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import OrderingFilter

from graphql import GraphQLError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from creator.studies.models import Study, Membership, MEMBER_ROLE_CHOICES
from creator.studies.schema import StudyNode

User = get_user_model()


class CollaboratorConnection(Connection):
    class Meta:
        abstract = True

    class Edge:
        """
        Extends relay edges on study-collaborator relationships to include
        information from the 'Membership' through-table.
        """

        # Need to referrence the node by module to avoid circular deps
        invited_by = Field("creator.users.schema.UserNode")
        joined_on = DateTime()
        # We need to manually convert the role field's choices into enums
        # that graphene understands
        role = convert_django_field_with_choices(
            Membership._meta.get_field("role")
        )

        def resolve_invited_by(root, info, **kwargs):
            """
            Returns the user that invited this collaborator to the study.
            """
            study_id = root._get_study_id(info)
            invited_by = Membership.objects.get(
                collaborator=root.node.id, study=study_id
            ).invited_by

            return invited_by

        def resolve_joined_on(root, info, **kwargs):
            """
            Returns the date the collaborator joined the study.
            """
            study_id = root._get_study_id(info)
            joined_on = Membership.objects.get(
                collaborator=root.node.id, study=study_id
            ).joined_on

            return joined_on

        def resolve_role(root, info, **kwargs):
            """
            Returns the role of the collaborator in the study.
            """
            study_id = root._get_study_id(info)
            role = (
                Membership.objects.filter(
                    collaborator=root.node.id, study=study_id
                )
                .first()
                .role
            )

            return role

        def _get_study_id(self, info):
            """
            The study id for which the user is a collaborator may be passed
            in as either the 'id' variable or the 'study' variable depending on
            which query is being executed.
            This attempts to resolve both and asserts that the id decoded is
            the expected StudyNode type.
            """
            gid = info.variable_values.get(
                "study"
            ) or info.variable_values.get("id")
            node_type, study_id = from_global_id(gid)
            assert node_type == "StudyNode"
            return study_id


class UserNode(DjangoObjectType):
    roles = List(String, description="Roles that the user has")

    def resolve_roles(self, info):
        return self.ego_roles

    class Meta:
        model = User
        interfaces = (relay.Node,)
        connection_class = CollaboratorConnection
        fields = [
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
            "studies",
            "groups",
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


class UpdateUserMutation(graphene.Mutation):
    """
    Updates user's groups
    """

    class Arguments:
        user = graphene.ID(required=True)
        groups = graphene.List(graphene.ID, required=False)

    user = graphene.Field(UserNode)

    def mutate(self, info, user, groups=None):
        """
        Updates a user
        """
        current_user = info.context.user
        if not current_user.has_perm("creator.change_user"):
            raise GraphQLError("Not allowed")

        _, user_id = from_global_id(user)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise GraphQLError("User does not exist.")

        if isinstance(groups, list):
            group_ids = [from_global_id(g)[1] for g in groups]
            group_objs = Group.objects.filter(id__in=group_ids).all()
            # If fewer groups were returned from the database than
            # were requested, one or more must not exist
            if len(group_objs) < len(groups):
                raise GraphQLError("Group does not exist.")
            user.groups.set(group_objs, clear=True)

        return UpdateUserMutation(user=user)


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
