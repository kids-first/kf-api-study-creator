import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id

from django.conf import settings
from creator.ingest_runs.nodes import IngestRunNode
from creator.ingest_runs.models import IngestRun


class CreateIngestRunInput(graphene.InputObjectType):
    """ Parameters used when creating a new ingest_run """

    name = graphene.String(description="The name of the ingest_run")


class UpdateIngestRunInput(graphene.InputObjectType):
    """ Parameters used when updating an existing ingest_run """

    name = graphene.String(description="The name of the ingest_run")


class CreateIngestRunMutation(graphene.Mutation):
    """ Creates a new ingest_run """

    class Arguments:
        input = CreateIngestRunInput(
            required=True, description="Attributes for the new ingest_run"
        )

    ingest_run = graphene.Field(IngestRunNode)

    def mutate(self, info, input):
        """
        Creates a new ingest_run.
        """
        user = info.context.user
        if not user.has_perm("ingest_runs.add_ingestrun"):
            raise GraphQLError("Not allowed")

        ingest_run = IngestRun()
        return CreateIngestRunMutation(ingest_run=ingest_run)


class UpdateIngestRunMutation(graphene.Mutation):
    """ Update an existing ingest_run """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the ingest_run to update"
        )
        input = UpdateIngestRunInput(
            required=True, description="Attributes for the ingest_run"
        )

    ingest_run = graphene.Field(IngestRunNode)

    def mutate(self, info, id, input):
        """
        Updates an existing ingest_run
        """
        user = info.context.user
        if not user.has_perm("ingest_runs.change_ingestrun"):
            raise GraphQLError("Not allowed")

        model, node_id = from_global_id(id)

        try:
            ingest_run = IngestRun.objects.get(id=node_id)
        except IngestRun.DoesNotExist:
            raise GraphQLError("IngestRun was not found")

        return UpdateIngestRunMutation(ingest_run=ingest_run)


class Mutation:
    """ Mutations for ingest_runs """

    create_ingest_run = CreateIngestRunMutation.Field(
        description="Create a new ingest_run."
    )
    update_ingest_run = UpdateIngestRunMutation.Field(
        description="Update a given ingest_run"
    )
