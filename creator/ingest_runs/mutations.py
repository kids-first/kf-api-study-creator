import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id
from django.db import transaction
from django.core.exceptions import ValidationError

from creator.ingest_runs.nodes import IngestRunNode
from creator.ingest_runs.models import IngestRun, State
from creator.ingest_runs.common.model import hash_versions
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

        # Create IngestRun for a set of file versions, if one does not exist
        # with same input_hash
        ingest_run = IngestRun()
        input_hash = hash_versions([v.kf_id for v in versions])

        # Check if duplicate IngestRuns exist
        irs_with_same_input_hash = IngestRun.objects.filter(
            state__in=[State.NOT_STARTED, State.RUNNING],
            input_hash=input_hash,
        ).all()

        if irs_with_same_input_hash.count() > 0:
            cancel_duplicate_ingest_runs(irs_with_same_input_hash)
        else:
            with transaction.atomic():
                ingest_run.save()
                ingest_run.creator = user
                ingest_run.versions.set(versions)
                ingest_run.save()

            ingest_run.queue.enqueue(
                run_ingest,
                args=(ingest_run.id,),
                job_id=str(ingest_run.id),
            )
        return StartIngestRunMutation(ingest_run=ingest_run)


def cancel_duplicate_ingest_runs(irs_with_same_input_hash):
    """
    Cancel duplicate IngestRuns. This is put into a separate function
    to make the unit tests simpler.
    """
    for ir in irs_with_same_input_hash:
        ir.queue.enqueue(cancel_ingest, args=(ir.id,))


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

        ingest_run.queue.enqueue(cancel_ingest, args=(str(ingest_run.id),))

        return CancelIngestRunMutation(ingest_run=ingest_run)


class Mutation:
    """ Mutations for ingest_runs """

    start_ingest_run = StartIngestRunMutation.Field(
        description="Start a new ingest_run."
    )
    cancel_ingest_run = CancelIngestRunMutation.Field(
        description="Cancel a given ingest_run"
    )
