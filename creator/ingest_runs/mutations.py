import graphene
import django_rq
from graphql import GraphQLError
from graphql_relay import from_global_id
from django.db import transaction
from django.core.exceptions import ValidationError
from creator.ingest_runs.nodes import IngestRunNode
from creator.ingest_runs.models import IngestRun
from creator.ingest_runs.tasks import run_ingest, cancel_ingest
from creator.files.models import Version


class StartIngestRunInput(graphene.InputObjectType):
    """ Parameters used when starting a new ingest_run """

    versions = graphene.List(
        graphene.ID,
        description=("File versions to be ingested"),
    )


class StartIngestRunMutation(graphene.Mutation):
    """ Start a new ingest_run """

    class Arguments:
        input = StartIngestRunInput(
            required=True, description="Attributes for the new ingest_run"
        )

    ingest_run = graphene.Field(IngestRunNode)

    def mutate(self, info, input):
        """
        Starts a new ingest_run.
        """
        user = info.context.user
        if not user.has_perm("ingest_runs.add_ingestrun"):
            raise GraphQLError("Not allowed")

        # Convert relay ids to Version objects
        version_ids = input.get("versions", [])
        if not version_ids:
            raise ValidationError(
                "An IngestRun must be started with at least 1 file Version"
            )

        versions = []
        for vid in version_ids:
            model, vid = from_global_id(vid)
            try:
                versions.append(Version.objects.get(kf_id=vid))
            except Version.DoesNotExist:
                raise GraphQLError(f"The Version {vid} does not exist")

        # Create ingest run for a set of file versions
        with transaction.atomic():
            ingest_run = IngestRun()
            ingest_run.save()
            ingest_run.versions.set(versions)
            ingest_run.save()

        uuid_str = str(ingest_run.id)
        django_rq.enqueue(
            run_ingest,
            args=(uuid_str,),
            job_id=uuid_str,
        )

        return StartIngestRunMutation(ingest_run=ingest_run)


class CancelIngestRunMutation(graphene.Mutation):
    """
    Cancel an existing ingest_run
    """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the ingest_run to cancel"
        )

    ingest_run = graphene.Field(IngestRunNode)

    def mutate(self, info, id):
        """
        Cancel an existing ingest_run
        """
        user = info.context.user
        if not user.has_perm("ingest_runs.cancel_ingestrun"):
            raise GraphQLError("Not allowed")

        model, obj_id = from_global_id(id)

        try:
            ingest_run = IngestRun.objects.get(id=obj_id)
        except IngestRun.DoesNotExist:
            raise GraphQLError(f"IngestRun {obj_id} was not found")

        django_rq.enqueue(cancel_ingest, args=(str(ingest_run.id),))

        return CancelIngestRunMutation(ingest_run=ingest_run)


class Mutation:
    """ Mutations for ingest_runs """

    start_ingest_run = StartIngestRunMutation.Field(
        description="Start a new ingest_run."
    )
    cancel_ingest_run = CancelIngestRunMutation.Field(
        description="Cancel a given ingest_run"
    )
