import graphene
import django_fsm
import django_rq
from graphql import GraphQLError
from graphql_relay import from_global_id

from django.conf import settings
from creator.releases.nodes import ReleaseNode
from creator.releases.models import Release
from creator.releases.tasks import publish


class CreateReleaseInput(graphene.InputObjectType):
    """ Parameters used when creating a new release """

    name = graphene.String(description="The name of the release")


class UpdateReleaseInput(graphene.InputObjectType):
    """ Parameters used when updating an existing release """

    name = graphene.String(description="The name of the release")


class CreateReleaseMutation(graphene.Mutation):
    """ Creates a new release """

    class Arguments:
        input = CreateReleaseInput(
            required=True, description="Attributes for the new release"
        )

    release = graphene.Field(ReleaseNode)

    def mutate(self, info, input):
        """
        Creates a new release.
        """
        user = info.context.user
        if not user.has_perm("releases.add_release"):
            raise GraphQLError("Not allowed")

        release = Release()
        return CreateReleaseMutation(release=release)


class UpdateReleaseMutation(graphene.Mutation):
    """ Update an existing release """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the release to update"
        )
        input = UpdateReleaseInput(
            required=True, description="Attributes for the release"
        )

    release = graphene.Field(ReleaseNode)

    def mutate(self, info, id, input):
        """
        Updates an existing release
        """
        user = info.context.user
        if not user.has_perm("releases.change_release"):
            raise GraphQLError("Not allowed")

        model, node_id = from_global_id(id)

        try:
            release = Release.objects.get(pk=node_id)
        except Release.DoesNotExist:
            raise GraphQLError("Release was not found")

        return UpdateReleaseMutation(release=release)


class PublishReleaseMutation(graphene.Mutation):
    """ Publish a release """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the release to publish"
        )

    release = graphene.Field(ReleaseNode)

    def mutate(self, info, id):
        """
        Publishes a release
        """
        user = info.context.user
        if not user.has_perm("releases.publish_release"):
            raise GraphQLError("Not allowed")

        model, node_id = from_global_id(id)

        try:
            release = Release.objects.get(pk=node_id)
        except Release.DoesNotExist:
            raise GraphQLError("Release was not found")

        release.publish()
        release.save()
        django_rq.enqueue(publish, release.pk)

        return PublishReleaseMutation(release=release)


class CancelReleaseMutation(graphene.Mutation):
    """ Cancel a release """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the release to cancel"
        )

    release = graphene.Field(ReleaseNode)

    def mutate(self, info, id):
        """
        Cancels a release
        """
        user = info.context.user
        if not user.has_perm("releases.cancel_release"):
            raise GraphQLError("Not allowed")

        model, node_id = from_global_id(id)

        try:
            release = Release.objects.get(pk=node_id)
        except Release.DoesNotExist:
            raise GraphQLError("Release was not found")

        release.cancel()
        release.save()

        return CancelReleaseMutation(release=release)


class Mutation:
    """ Mutations for releases """

    create_release = CreateReleaseMutation.Field(
        description="Create a new release."
    )
    update_release = UpdateReleaseMutation.Field(
        description="Update a given release"
    )
    publish_release = PublishReleaseMutation.Field(
        description="Publish a given release"
    )
    cancel_release = CancelReleaseMutation.Field(
        description="Cancel a given release"
    )
