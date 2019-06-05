import graphene
import django_filters
from graphene import relay, ObjectType, Field
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import OrderingFilter

from graphql import GraphQLError
from django.contrib.auth import get_user_model

from creator.studies.models import Study

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
            "picture",
            "study_subscriptions",
            "slack_notify",
            "slack_member_id",
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

    user = graphene.Field(UserNode)

    def mutate(self, info, **kwargs):
        """
        Updates a user's profile.
        Only applies to the request's current user
        """
        user = info.context.user
        if not user.is_authenticated or user is None or user.email == "":
            raise GraphQLError("Not authenticated to mutate profile")

        if kwargs.get("slack_notify"):
            user.slack_notify = kwargs.get("slack_notify")
        if kwargs.get("slack_member_id"):
            user.slack_member_id = kwargs.get("slack_member_id")
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
        if not user.is_authenticated or user is None or user.email == "":
            raise GraphQLError("not authenticated as a user with a profile")

        return user
