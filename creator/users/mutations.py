import graphene
from graphql_relay import from_global_id
from graphql import GraphQLError

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from creator.studies.models import Study

User = get_user_model()


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

    user = graphene.Field("creator.users.schema.UserNode")

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

    user = graphene.Field("creator.users.schema.UserNode")

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
    user = graphene.Field("creator.users.schema.UserNode")

    def mutate(self, info, study_id, **kwargs):
        """
        Adds a study to the user's study subscriptions
        """
        user = info.context.user
        if user is None or not user.is_authenticated:
            raise GraphQLError("Not allowed")

        try:
            study = Study.objects.get(kf_id=study_id)
        except Study.DoesNotExist:
            raise GraphQLError("Study does not exist.")

        if not (
            user.has_perm("studies.subscribe_study")
            or (
                user.has_perm("studies.subscribe_my_study")
                and user.studies.filter(kf_id=study.kf_id).exists()
            )
        ):
            raise GraphQLError("Not allowed")

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
    user = graphene.Field("creator.users.schema.UserNode")

    def mutate(self, info, study_id, **kwargs):
        """
        Removes a study from the user's study subscriptions
        """
        user = info.context.user
        if user is None or not user.is_authenticated:
            raise GraphQLError("Not allowed")

        try:
            study = Study.objects.get(kf_id=study_id)
        except Study.DoesNotExist:
            raise GraphQLError("Study does not exist.")

        if not (
            user.has_perm("studies.unsubscribe_study")
            or (
                user.has_perm("studies.unsubscribe_my_study")
                and user.studies.filter(kf_id=study.kf_id).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        # Remove the study to the users subscriptions
        user.study_subscriptions.remove(study)

        return SubscribeToMutation(success=True, user=user)


class Mutation(graphene.ObjectType):
    subscribe_to = SubscribeToMutation.Field(
        description="Subscribe the current user to a study"
    )
    unsubscribe_from = UnsubscribeFromMutation.Field(
        description="Unsubscribe the current user from a study"
    )
    update_my_profile = MyProfileMutation.Field(
        description="Update the currently logged in user's profile"
    )
    update_user = UpdateUserMutation.Field(description="Update a user")
