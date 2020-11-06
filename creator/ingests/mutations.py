import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id

from django.conf import settings
from creator.ingests.nodes import IngestRunNode
from creator.ingests.models import IngestRun
from creator.ingests.tasks import run_ingest, cancel_ingest


class StartIngestRunInput(graphene.InputObjectType):
    """ Parameters used when creating a new ingest """

    versions = graphene.List(
        graphene.ID,
        required=Tru,
        description="Versions to include in this ingest run",
    )


class StartIngestRunMutation(graphene.Mutation):
    """ Starts a new ingest run """

    class Arguments:
        input = CreateIngestRunInput(
            required=True, description="Attributes for the new ingest"
        )

    ingest_run = graphene.Field(IngestRunNode)

    def mutate(self, info, input):
        """
        Creates a new ingest.
        """
        user = info.context.user
        if not user.has_perm("ingests.add_ingestrun"):
            raise GraphQLError("Not allowed")

        if len(input.get("versions")) == 0:
            raise GraphQLError("Must specify at lest one version for ingest")

        versions = []
        for version_id in input.get("versions", []):
            model, node_id = from_global_id(version_id)
            try:
                versions.append(Version.objects.get(pk=node_id))
            except Version.DoesNotExist:
                raise GraphQLError("Version was not found")

        ingest_run = IngestRun()
        ingest_run.save()
        ingest_run.versions.set(versions)
        ingest_run.save()

        django_rq.enqueue(run_ingest, ingest_run_id=ingest_run.id)

        return StartIngestRunMutation(ingest=ingest_run)


class CancelIngestRunMutation(graphene.Mutation):
    """ Cancel an ingest run """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the ingest to update"
        )

    ingest_run = graphene.Field(IngestRunNode)

    def mutate(self, info, id, input):
        """
        Cancel an ingest run
        """
        user = info.context.user
        if not user.has_perm("ingests.cancel_ingestrun"):
            raise GraphQLError("Not allowed")

        model, node_id = from_global_id(id)

        try:
            ingest_run = IngestRun.objects.get(id=node_id)
        except IngestRun.DoesNotExist:
            raise GraphQLError("IngestRun was not found")

        # It could be sufficient to just set state without enqueueing
        django_rq.enqueue(cancel_ingest, ingest_run.pk)

        return CancelIngestRunMutation(ingest_run=ingest_run)


class Mutation:
    """ Mutations for ingests """

    start_ingest = StartIngestRunMutation.Field(
        description="Start a new ingest run."
    )
    cancel_ingest = CancelIngestRunMutation.Field(
        description="Cancel a given ingest run"
    )
