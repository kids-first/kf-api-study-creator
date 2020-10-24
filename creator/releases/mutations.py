import graphene
import django_fsm
import django_rq
from graphql import GraphQLError
from graphql_relay import from_global_id
from django.conf import settings

from creator.studies.models import Study
from creator.releases.nodes import ReleaseNode
from creator.releases.models import Release, ReleaseTask, ReleaseService
from creator.releases.tasks import initialize_release, publish_release


class StartReleaseInput(graphene.InputObjectType):
    """ Parameters used when creating a new release """

    name = graphene.String(description="The name of the release")
    description = graphene.String(description="The description of the release")
    is_major = graphene.Boolean(
        required=False, description="If this is a major release"
    )
    studies = graphene.List(
        graphene.ID,
        required=True,
        description="Studies to include in this release",
    )
    services = graphene.List(
        graphene.ID,
        required=True,
        description="Services to run in this release",
    )


class StartReleaseMutation(graphene.Mutation):
    """ Starts a new release """

    class Arguments:
        input = StartReleaseInput(
            required=True, description="Attributes for the new release"
        )

    release = graphene.Field(ReleaseNode)

    def mutate(self, info, input):
        """
        Starts a new release.
        """
        user = info.context.user
        if not user.has_perm("releases.add_release"):
            raise GraphQLError("Not allowed")

        studies = []
        # Make sure all the studies resolve
        for study in input["studies"]:

            _, study_id = from_global_id(study)
            try:
                study = Study.objects.get(pk=study_id)
            except Study.DoesNotExist:
                raise GraphQLError(f"Study {study_id} does not exist")
            studies.append(study)

        services = []
        # Make sure all the services resolve
        for service in input["services"]:
            _, service_id = from_global_id(service)
            try:
                service = ReleaseService.objects.get(pk=service_id)
            except ReleaseService.DoesNotExist:
                raise GraphQLError(f"Service {service_id} does not exist")
            services.append(service)

        # Create the release first before creating the tasks
        release = Release(
            name=input["name"],
            description=input["description"],
            is_major=input["is_major"],
            creator=user,
        )
        # Need to save the release before we can add study relations
        release.save()
        release.studies.set(studies)

        # Now make tasks for each service since we know they all exist
        # and the release has been created to tie them to
        for service in services:
            task = ReleaseTask(release=release, release_service=service)
            task.save()

        django_rq.enqueue(initialize_release, release.pk)

        release.initialize()
        release.save()

        return StartReleaseMutation(release=release)


class UpdateReleaseInput(graphene.InputObjectType):
    """ Parameters used when updating an existing release """

    name = graphene.String(description="The name of the release")


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
            raise GraphQLError(f"Release {node_id} does not exist")

        return UpdateReleaseMutation(release=release)


class PublishReleaseMutation(graphene.Mutation):
    """ Publish a release """

    class Arguments:
        release = graphene.ID(
            required=True, description="The ID of the release to publish"
        )

    release = graphene.Field(ReleaseNode)

    def mutate(self, info, release):
        """
        Publishes a release
        """
        user = info.context.user
        if not user.has_perm("releases.publish_release"):
            raise GraphQLError("Not allowed")

        model, node_id = from_global_id(release)

        try:
            release = Release.objects.get(pk=node_id)
        except Release.DoesNotExist:
            raise GraphQLError(f"Release {node_id} does not exist")

        release.publish()
        release.save()
        django_rq.enqueue(publish_release, release.pk)

        return PublishReleaseMutation(release=release)


class CancelReleaseMutation(graphene.Mutation):
    """ Cancel a release """

    class Arguments:
        release = graphene.ID(
            required=True, description="The ID of the release to cancel"
        )

    release = graphene.Field(ReleaseNode)

    def mutate(self, info, release):
        """
        Cancels a release
        """
        user = info.context.user
        if not user.has_perm("releases.cancel_release"):
            raise GraphQLError("Not allowed")

        model, node_id = from_global_id(release)

        try:
            release = Release.objects.get(pk=node_id)
        except Release.DoesNotExist:
            raise GraphQLError(f"Release {node_id} does not exist")

        release.cancel()
        release.save()

        return CancelReleaseMutation(release=release)


class Mutation:
    """ Mutations for releases """

    start_release = StartReleaseMutation.Field(
        description="Start a new release."
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
