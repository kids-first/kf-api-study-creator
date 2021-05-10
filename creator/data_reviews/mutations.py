from django_fsm import TransitionNotAllowed
import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id
from django.db import transaction

from creator.data_reviews.nodes import DataReviewNode
from creator.studies.models import Study
from creator.files.models import Version
from creator.data_reviews.models import DataReview, State
from creator.ingest_runs.models import ValidationResultset


def check_review_files(input, data_review):
    """
    Validate version ids in the create/update data review mutation input

    Convert base64 encoded Version ids to Version primary keys
    Check if file versions exist and they are from same study
    Check if input file versions are different than existing review versions

    :param input: input parameters from create/update data review mutation
    :type input: dict
    :param data_review: current data review object being created or updated
    :type data_review: DataReview

    :returns: list of version ids if version ids are valid or None if
    there are no version ids in the input or the input versions didn't change
    from the existing version ids in the data_review
    """
    if "versions" not in input:
        return None

    input_version_ids = []
    for v in input["versions"]:
        _, version_id = from_global_id(v)
        input_version_ids.append(version_id)

    # Check all versions exist
    versions = (
        Version.objects.filter(pk__in=input_version_ids)
        .select_related("root_file__study")
        .all()
    )
    if len(versions) != len(input["versions"]):
        raise GraphQLError(
            "Error in modifying data_review. All file versions in data "
            "review must exist."
        )

    # Check all versions come from same study
    studies = set(
        [v.root_file.study.pk for v in versions] + [data_review.study.pk]
    )
    if len(studies) > 1:
        raise GraphQLError(
            "Error in modifying data_review. All file versions in data "
            "review must have files that belong to the same study."
        )

    # Check if data review file versions changed
    if data_review:
        if set(data_review.versions.values_list("pk", flat=True)) == set(
            input_version_ids
        ):
            input_version_ids = None

    return input_version_ids


class CreateDataReviewInput(graphene.InputObjectType):
    """ Parameters used when creating a new data_review """

    name = graphene.String(
        required=True, description="The name of the data_review"
    )
    description = graphene.String(
        required=True, description="The description of the data_review"
    )
    study = graphene.ID(
        required=True,
        description="The ID of the study this data_review is for",
    )
    versions = graphene.List(
        graphene.ID,
        description="File versions in this data_review",
    )


class UpdateDataReviewInput(graphene.InputObjectType):
    """ Parameters used when updating an existing data_review """

    name = graphene.String(description="The name of the data_review")
    description = graphene.String(
        description="The description of the data_review"
    )
    versions = graphene.List(
        graphene.ID,
        description="File versions in this data_review",
    )


class CreateDataReviewMutation(graphene.Mutation):
    """ Creates a new data_review """

    class Arguments:
        input = CreateDataReviewInput(
            required=True, description="Attributes for the new data_review"
        )

    data_review = graphene.Field(DataReviewNode)

    def mutate(self, info, input):
        """
        Creates a new data_review.
        """
        user = info.context.user

        # Check if study exists
        _, study_id = from_global_id(input["study"])
        try:
            study = Study.objects.get(pk=study_id)
        except Study.DoesNotExist:
            raise GraphQLError(f"Study {study_id} not found.")

        # Check permissions
        # Must have general add permission for any study OR
        # permission to add review to user's studies
        if not (
            user.has_perm("data_reviews.add_datareview")
            or (
                user.has_perm("data_reviews.add_my_study_datareview")
                and user.studies.filter(kf_id=study.kf_id).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        # Create data_review
        with transaction.atomic():
            data_review = DataReview(
                **{
                    k: input[k]
                    for k in input
                    if k not in {"study", "versions"}
                }
            )
            data_review.study = study
            data_review.creator = user
            data_review.save()

            # Check files in review
            review_version_ids = check_review_files(input, data_review)

            # Review files are valid and they've changed
            if review_version_ids:
                # Update versions
                data_review.versions.set(review_version_ids)

                # Clear the data review's validation results if they exist
                try:
                    data_review.validation_resultset.delete()
                except ValidationResultset.DoesNotExist:
                    pass

                # Start review if we have files
                data_review.start()
                data_review.save()

        return CreateDataReviewMutation(data_review=data_review)


class UpdateDataReviewMutation(graphene.Mutation):
    """ Update an existing data_review """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the data_review to update"
        )
        input = UpdateDataReviewInput(
            required=True, description="Attributes for the data_review"
        )

    data_review = graphene.Field(DataReviewNode)

    def mutate(self, info, id, input):
        """
        Updates an existing data_review
        """
        user = info.context.user

        model, node_id = from_global_id(id)
        try:
            data_review = DataReview.objects.get(pk=node_id)
        except DataReview.DoesNotExist:
            raise GraphQLError("DataReview was not found")

        # Check permissions
        # Must have general change review permission for any study OR
        # permission to change review for user's studies
        if not (
            user.has_perm("data_reviews.change_datareview")
            or (
                user.has_perm("data_reviews.change_my_study_datareview")
                and user.studies.filter(kf_id=data_review.study.kf_id).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        # Closed/Completed reviews cannot be modified
        if data_review.state in {State.CLOSED, State.COMPLETED}:
            raise GraphQLError(
                "Cannot modify a data review that has been closed or "
                "completed. However, a closed review can be re-opened and "
                "then modified."
            )

        # Update data_review
        with transaction.atomic():
            for attr in ["name", "description"]:
                if attr in input:
                    setattr(data_review, attr, input[attr])

            # Check files in review
            review_version_ids = check_review_files(input, data_review)
            if review_version_ids is not None:
                # Start review if not started
                if data_review.state == State.NOT_STARTED:
                    data_review.start()

                # We received updates while waiting, go back to reviewing state
                elif data_review.state == State.WAITING:
                    data_review.receive_updates()

                data_review.versions.set(review_version_ids)
            data_review.save()

        return UpdateDataReviewMutation(data_review=data_review)


def mutate_state_helper(info, id, state_change_method_name):
    """
    Helper for a take action review mutation (e.g. approve, close, reopen)
    Mutate data_review.state
    """
    user = info.context.user

    data_review = None
    model, node_id = from_global_id(id)
    try:
        data_review = DataReview.objects.get(pk=node_id)
    except DataReview.DoesNotExist:
        raise GraphQLError("DataReview was not found")

    # Check permissions
    # Must have general change review permission for any study OR
    # permission to change review for user's studies
    if not (
        user.has_perm("data_reviews.change_datareview")
        or (
            user.has_perm("data_reviews.change_my_study_datareview")
            and user.studies.filter(kf_id=data_review.study.kf_id).exists()
        )
    ):
        raise GraphQLError("Not allowed")

    # Take review action - e.g. approve, close, reopen
    state_change_method = getattr(data_review, state_change_method_name)
    try:
        state_change_method()
    except TransitionNotAllowed:
        raise GraphQLError(
            f"Cannot {state_change_method_name} data review when data review "
            f"is in state: {data_review.state}"
        )

    data_review.save()

    return data_review


class AwaitDataReviewMutation(graphene.Mutation):
    """ Wait for updates for a data_review """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the data_review"
        )

    data_review = graphene.Field(DataReviewNode)

    def mutate(self, info, id):
        """
        Update data_review state to State.WAITING
        """
        data_review = mutate_state_helper(info, id, "wait_for_updates")
        return AwaitDataReviewMutation(data_review=data_review)


class ApproveDataReviewMutation(graphene.Mutation):
    """ Approve a data_review """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the data_review to approve"
        )

    data_review = graphene.Field(DataReviewNode)

    def mutate(self, info, id):
        """
        Update data_review state to State.COMPLETE
        """
        data_review = mutate_state_helper(info, id, "approve")
        return ApproveDataReviewMutation(data_review=data_review)


class CloseDataReviewMutation(graphene.Mutation):
    """ Close an incomplete data_review """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the data_review to close"
        )

    data_review = graphene.Field(DataReviewNode)

    def mutate(self, info, id):
        """
        Update data_review state to State.CLOSED
        """
        data_review = mutate_state_helper(info, id, "close")
        return CloseDataReviewMutation(data_review=data_review)


class ReopenDataReviewMutation(graphene.Mutation):
    """ Re-open a closed data_review """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the data_review to re-open"
        )

    data_review = graphene.Field(DataReviewNode)

    def mutate(self, info, id):
        """
        Update data_review state to State.IN_REVIEW
        """
        data_review = mutate_state_helper(info, id, "reopen")
        return ReopenDataReviewMutation(data_review=data_review)


class Mutation:
    """ Mutations for data_reviews """

    create_data_review = CreateDataReviewMutation.Field(
        description="Create a new data_review."
    )
    update_data_review = UpdateDataReviewMutation.Field(
        description="Update a given data_review"
    )
    await_data_review = AwaitDataReviewMutation.Field(
        description="Wait for updates for a data_review."
    )
    approve_data_review = ApproveDataReviewMutation.Field(
        description="Approve a data_review."
    )
    close_data_review = CloseDataReviewMutation.Field(
        description="Close an incomplete data_review."
    )
    reopen_data_review = ReopenDataReviewMutation.Field(
        description="Re-open a closed data_review."
    )
