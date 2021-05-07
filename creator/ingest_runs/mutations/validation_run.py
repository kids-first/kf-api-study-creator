import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id
from django.db import transaction

from creator.ingest_runs.nodes import ValidationRunNode
from creator.ingest_runs.models import ValidationRun
from creator.ingest_runs.tasks import run_validation, cancel_validation
from creator.ingest_runs.common.mutations import (
    cancel_duplicate_ingest_processes,
)
from creator.files.models import Version
from creator.data_reviews.models import DataReview


class StartValidationRunInput(graphene.InputObjectType):
    """ Parameters used when starting a new validation_run """

    data_review = graphene.ID(
        required=True,
        description=("The data review whose file versions will be validated"),
    )


class StartValidationRunMutation(graphene.Mutation):
    """ Start a new validation_run """

    class Arguments:
        input = StartValidationRunInput(
            required=True, description="Attributes for the new validation_run"
        )

    validation_run = graphene.Field(ValidationRunNode)

    def mutate(self, info, input):
        """
        Starts a new validation_run.
        """
        user = info.context.user

        # -- Get versions from data review --
        # Data review must exist
        dr = input.get("data_review")
        if not dr:
            raise GraphQLError(
                "A validation run must be started for an existing data review"
            )

        _, dr_id = from_global_id(dr)
        try:
            data_review = (
                DataReview.objects.only("kf_id", "study__kf_id")
                .select_related("study").get(pk=dr_id)
            )
        except DataReview.DoesNotExist:
            raise GraphQLError(
                "DataReview was not found. A validation run must be started "
                "for an existing data review."
            )

        # Check permissions
        # Must have general start validation permission for any study OR
        # permission to start validation for user's studies
        if not (
            user.has_perm("ingest_runs.add_validationrun")
            or (
                user.has_perm("ingest_runs.add_my_study_validationrun")
                and user.studies.filter(kf_id=data_review.study.kf_id).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        # Versions must exist
        version_ids = (
            Version.objects.filter(data_reviews__pk=dr_id)
            .values_list("pk", flat=True)
        )
        if len(version_ids) == 0:
            raise GraphQLError(
                "An validation run must be started with at least "
                "1 file version"
            )

        # Create ValidationRun for a set of file versions,
        # if one does not exist with same input_hash
        if not cancel_duplicate_ingest_processes(
            version_ids, ValidationRun, cancel_validation
        ):
            with transaction.atomic():
                validation_run = ValidationRun()
                validation_run.creator = user
                validation_run.data_review = data_review
                validation_run.save()

            # Transition to initializing state
            validation_run.initialize()
            validation_run.save()

            validation_run.queue.enqueue(
                run_validation,
                args=(str(validation_run.id),),
                job_id=str(validation_run.id),
            )
        return StartValidationRunMutation(validation_run=validation_run)


class CancelValidationRunMutation(graphene.Mutation):
    """
    Cancel an existing validation_run
    """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the validation_run to cancel"
        )

    validation_run = graphene.Field(ValidationRunNode)

    def mutate(self, info, id):
        """
        Cancel an existing validation_run
        """
        user = info.context.user
        _, vr_id = from_global_id(id)

        try:
            validation_run = (
                ValidationRun.objects.select_related("data_review__study")
                .only("data_review__study__kf_id", "state").get(pk=vr_id)
            )
        except ValidationRun.DoesNotExist:
            raise GraphQLError(f"Validation_run {vr_id} was not found")

        # Check permissions
        # Must have general cancel validation permission for any study OR
        # permission to cancel validation for user's studies
        if not (
            user.has_perm("ingest_runs.cancel_validationrun")
            or (
                user.has_perm("ingest_runs.cancel_my_study_validationrun")
                and user.studies.filter(
                    kf_id=validation_run.study.kf_id
                ).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        # Transition to canceling state
        validation_run.start_cancel()
        validation_run.save()

        validation_run.queue.enqueue(
            cancel_validation, args=(str(validation_run.id),)
        )

        return CancelValidationRunMutation(validation_run=validation_run)


class Mutation:
    """ Mutations for validation_runs """

    start_validation_run = StartValidationRunMutation.Field(
        description="Start a new validation_run."
    )
    cancel_validation_run = CancelValidationRunMutation.Field(
        description="Cancel a given validation_run"
    )
