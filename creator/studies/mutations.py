"""
Contains mutations for studies
"""
import json
import logging
import graphene
import requests
import django_rq

from dateutil.parser import parse
from graphql import GraphQLError
from graphql_relay import from_global_id

from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from creator.tasks import setup_bucket_task
from creator.tasks import setup_cavatica_task
from creator.tasks import setup_slack_task
from creator.users.schema import CollaboratorConnection
from creator.organizations.models import Organization
from creator.studies.models import Study, Membership
from creator.studies.schema import StudyNode
from creator.studies.nodes import (
    SequencingStatusType,
    IngestionStatusType,
    PhenotypeStatusType,
)
from creator.events.models import Event

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
User = get_user_model()


def sanitize_fields(attributes):
    """
    This selects out only the valid dataservice fields to ensure that we
    don't try to post any additional fields to the dataservice, which will
    cause it to fail
    """
    fields = {
        "name",
        "visible",
        "attribution",
        "data_access_authority",
        "external_id",
        "release_status",
        "short_name",
        "version",
    }
    return {k: attributes[k] for k in attributes.keys() & fields}


def get_collaborators(input):
    """
    Convert a list of relay ids of collaborators into a list of User objects
    """
    collaborators = input.get("collaborators", [])

    users = []
    for collab in collaborators:
        model, collab_id = from_global_id(collab)
        try:
            users.append(User.objects.get(id=int(collab_id)))
        except (User.DoesNotExist, TypeError):
            raise GraphQLError("A provided user does not exist")

    return users


class StudyInput(graphene.InputObjectType):
    """ Schema for input to create and update study mutations """

    # These fields are from the study model in dataservice
    name = graphene.String(description="The full name of the study")
    visible = graphene.Boolean(
        description="Whether or not the study is visible in the dataservice"
    )

    attribution = graphene.String(
        description="URL providing more information about the study"
    )
    data_access_authority = graphene.String(
        description="The organization that moderates access to the study"
    )
    external_id = graphene.String(
        required=False,
        description=(
            "The primary identifier this study is know by outside of "
            "Kids-First, often the dbGaP phsid."
        ),
    )
    release_status = graphene.String(
        description="Release status as set in the dataservice"
    )
    short_name = graphene.String(
        description=(
            "Short name of the study for use in space-restricted containers"
        )
    )
    version = graphene.String(
        description=(
            "Study version, often the provided by the data access authority"
        )
    )

    # These fields are unique to study-creator
    description = graphene.String(
        description="Study description, often a grant abstract"
    )
    anticipated_samples = graphene.Int(
        description="Number of expected samples for this study"
    )
    awardee_organization = graphene.String(
        description="Organization associated with the X01 grant"
    )
    release_date = graphene.Date(
        description=(
            "Date that this study is expected to be released to the public"
        )
    )
    investigator_name = graphene.String(
        description="The name of the principle investigator of this study"
    )
    bucket = graphene.String(
        description="The s3 bucket where data for this study resides"
    )
    slack_channel = graphene.String(
        description="The Slack channel name of the study"
    )
    slack_notify = graphene.Boolean(
        description="Whether enabled slack notifications for study updates"
    )
    additional_fields = graphene.JSONString(
        description="Capture any additional/non-standard fields for each study"
    )


class CreateStudyInput(StudyInput):
    """ Schema for creating a new study """

    collaborators = graphene.List(
        graphene.ID,
        description=(
            "Users related to the study. "
            "If null, the collaborators will not be modified."
        ),
    )
    organization = graphene.ID(
        description="The organization to create the study in.", required=True
    )


class CreateStudyMutation(graphene.Mutation):
    """ Mutation to create a new study """

    class Arguments:
        """ Arguments for creating a new study """

        input = CreateStudyInput(
            required=True, description="Attributes for the new study"
        )
        workflows = graphene.List(
            graphene.String,
            description="Workflows to be run for this study",
            required=False,
        )

    study = graphene.Field(StudyNode)

    def mutate(self, info, input, workflows=None):
        """
        Creates a new study in the specified organization.
        If FEAT_DATASERVICE_CREATE_STUDIES is enabled, try to first create
        the study in the dataservice. If the request fails, no study will be
        saved in the creator's database
        If FEAT_DATASERVICE_CREATE_STUDIES is not enabled, we will still
        create the study, but it will be labeled as a local study.
        """
        user = info.context.user
        if not user.has_perm("studies.add_study"):
            raise GraphQLError("Not allowed")

        try:
            _, org_id = from_global_id(input.get("organization"))
            organization = Organization.objects.get(pk=org_id)
        except (Organization.DoesNotExist, ValidationError):
            raise GraphQLError(f"Organization {org_id} does not exist.")

        # Error if this feature is not enabled
        if not (
            settings.FEAT_DATASERVICE_CREATE_STUDIES
            and settings.DATASERVICE_URL
        ):
            raise GraphQLError(
                "Creating studies is not enabled. "
                "You may need to make sure that the api is configured with a "
                "valid dataservice url and FEAT_DATASERVICE_CREATE_STUDIES "
                "has been set."
            )

        attributes = sanitize_fields(input)
        logger.info("Creating a new study in Data Service")
        try:
            resp = requests.post(
                f"{settings.DATASERVICE_URL}/studies",
                json=attributes,
                timeout=settings.REQUESTS_TIMEOUT,
                headers=settings.REQUESTS_HEADERS,
            )
            # Try decoding the json payload to verify it's valid
            resp.json()
        except (
            requests.exceptions.RequestException,
            json.decoder.JSONDecodeError,
        ) as e:
            logger.error(f"Problem creating study in Data Service: {e}")
            raise GraphQLError(f"Problem creating study in Data Service: {e}")

        # Raise an error if it looks like study failed to create
        if not resp.status_code == 201 or "results" not in resp.json():
            error = resp.json()
            if "_status" in error:
                error = error["_status"]
            if "message" in error:
                error = error["message"]
            logger.error(f"Problem creating study: {error}")
            raise GraphQLError(f"Problem creating study: {error}")

        logger.info(
            f"Created new study in Data Service: "
            f"{resp.json()['results']['kf_id']}"
        )

        collaborators = get_collaborators(input)
        if "collaborators" in input:
            del input["collaborators"]
        if "organization" in input:
            del input["organization"]

        # Merge dataservice response attributes with the original input
        attributes = {**input, **resp.json()["results"]}
        created_at = attributes.get("created_at")
        if created_at:
            attributes["created_at"] = parse(created_at)
        attributes["deleted"] = False
        study = Study(organization=organization, **attributes)
        study.save()

        # Add any specified users as collaborators
        for collaborator in collaborators:
            membership = Membership(
                study=study, collaborator=collaborator, invited_by=user
            ).save()

        # Log an event
        message = f"{user.display_name} created study {study.kf_id}"
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="SD_CRE",
        )
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        # Setup bucket
        bucket_job = None
        if (
            settings.FEAT_STUDY_BUCKETS_CREATE_BUCKETS
            and settings.STUDY_BUCKETS_REGION
            and settings.STUDY_BUCKETS_LOGGING_BUCKET
            and settings.STUDY_BUCKETS_DR_LOGGING_BUCKET
            and settings.STUDY_BUCKETS_REPLICATION_ROLE
            and settings.STUDY_BUCKETS_INVENTORY_LOCATION
        ):
            logger.info(f"Scheduling bucket setup for study {study.kf_id}")
            bucket_job = django_rq.enqueue(setup_bucket_task, study.kf_id)
        else:
            logger.info(
                f"Bucket setup integration not configured. Skipping setup of"
                f"new bucket resources for study {study.kf_id}"
            )

        # Setup Cavatica
        if (
            settings.FEAT_CAVATICA_CREATE_PROJECTS
            and settings.CAVATICA_URL
            and settings.CAVATICA_HARMONIZATION_TOKEN
            and settings.CAVATICA_DELIVERY_TOKEN
        ):
            logger.info(
                f"Scheduling Cavatica project setup for study {study.kf_id}"
            )
            cav_job = django_rq.enqueue(
                setup_cavatica_task,
                study.kf_id,
                workflows,
                user.sub,
                depends_on=bucket_job,
            )
        else:
            logger.info(
                f"Cavatica integration not configured. Skipping setup of "
                f"new projects for study {study.kf_id}"
            )

        # Setup Slack
        if settings.FEAT_SLACK_CREATE_CHANNELS:
            logger.info(
                f"Scheduling Slack channel setup for study {study.kf_id}"
            )
            slack_job = django_rq.enqueue(setup_slack_task, study.kf_id)
        else:
            logger.info(
                f"Slack integration not configured. Skipping setup of "
                f"new Slack channel for study {study.kf_id}"
            )

        return CreateStudyMutation(study=study)


class UpdateStudyMutation(graphene.Mutation):
    """ Mutation to update an existing study """

    class Arguments:
        """ Arguments to update an existing study """

        id = graphene.ID(
            required=True, description="The ID of the study to update"
        )
        input = StudyInput(
            required=True, description="Attributes for the new study"
        )

    study = graphene.Field(StudyNode)

    def mutate(self, info, id, input):
        """
        Updates an existing study
        If FEAT_DATASERVICE_UPDATE_STUDIES is enabled, try to first update
        the study in the dataservice. If the request fails, no study will be
        updated in the creator's database
        """
        user = info.context.user
        if not user.has_perm("studies.change_study"):
            raise GraphQLError("Not allowed")

        # Error if this feature is not enabled
        if not (
            settings.FEAT_DATASERVICE_UPDATE_STUDIES
            and settings.DATASERVICE_URL
        ):
            raise GraphQLError(
                "Updating studies is not enabled. "
                "You may need to make sure that the api is configured with a "
                "valid dataservice url and FEAT_DATASERVICE_UPDATE_STUDIES "
                "has been set."
            )

        # Translate relay id to kf_id
        model, kf_id = from_global_id(id)
        study = Study.objects.get(kf_id=kf_id)

        attributes = sanitize_fields(input)

        try:
            resp = requests.patch(
                f"{settings.DATASERVICE_URL}/studies/{kf_id}",
                json=attributes,
                timeout=settings.REQUESTS_TIMEOUT,
                headers=settings.REQUESTS_HEADERS,
            )
        except requests.exceptions.RequestException as e:
            raise GraphQLError(f"Problem updating study: {e}")

        # Raise an error if it looks like study failed to update
        if not resp.status_code == 200 or "results" not in resp.json():
            error = resp.json()
            if "_status" in error:
                error = error["_status"]
            if "message" in error:
                error = error["message"]
            raise GraphQLError(f"Problem updating study: {error}")

        # We will update with the attributes received from dataservice to
        # ensure we are completely in-sync and merge  with the original input
        attributes = {**input, **resp.json()["results"]}
        if "created_at" in attributes:
            attributes["created_at"] = parse(attributes["created_at"])
        for attr, value in attributes.items():
            setattr(study, attr, value)
        study.save()

        # Log an event
        message = f"{user.display_name} updated study {study.kf_id}"
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="SD_UPD",
        )
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return CreateStudyMutation(study=study)


class AddCollaboratorMutation(graphene.Mutation):
    """ Mutation to add a collaborator to a study """

    class Arguments:
        """ Arguments to add a collaborator to a study """

        study = graphene.ID(
            required=True,
            description="The ID of the study to add the collaborator to",
        )
        user = graphene.ID(
            required=True,
            description="The ID of the user to add the to the study",
        )
        # The role property on the custom edge has a graphene enum type
        # associated with it so it will validate and resolve correctly
        role = CollaboratorConnection.Edge.role

    study = graphene.Field(StudyNode)

    def mutate(self, info, study, user, role):
        """
        Add a user as a collaborator to a study
        """
        user_id = user
        user = info.context.user
        if not user.has_perm("studies.add_collaborator"):
            raise GraphQLError("Not allowed")

        try:
            _, study_id = from_global_id(study)
            study = Study.objects.get(kf_id=study_id)
        except (Study.DoesNotExist):
            raise GraphQLError(f"Study {study_id} does not exist.")

        try:
            _, user_id = from_global_id(user_id)
            collaborator = User.objects.get(id=int(user_id))
        except (User.DoesNotExist, TypeError):
            raise GraphQLError(f"User {user_id} does not exist.")

        membership, created = Membership.objects.update_or_create(
            study=study, collaborator=collaborator, defaults={"role": role},
        )

        # Log an event
        if created:
            membership.invited_by = user
            message = (
                f"{user.display_name} added {collaborator.display_name} "
                f"as collaborator to study {study.kf_id}"
            )
            event = Event(
                organization=study.organization,
                study=study,
                description=message,
                event_type="CB_ADD",
            )
        else:
            message = (
                f"{user.display_name} changed {collaborator.display_name}'s "
                f"role to {role} in study {study.kf_id}"
            )
            event = Event(
                organization=study.organization,
                study=study,
                description=message,
                event_type="CB_UPD",
            )
        membership.save()
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return AddCollaboratorMutation(study=study)


class RemoveCollaboratorMutation(graphene.Mutation):
    """ Mutation to remove a collaborator from a study """

    class Arguments:
        """ Arguments to remove a collaborator from a study """

        study = graphene.ID(
            required=True,
            description="The ID of the study to remove the collaborator from",
        )
        user = graphene.ID(
            required=True,
            description="The ID of the user to remove from the study",
        )

    study = graphene.Field(StudyNode)

    def mutate(self, info, study, user):
        """
        Remove a user as a collaborator to a study
        """
        user_id = user
        user = info.context.user
        if not user.has_perm("studies.remove_collaborator"):
            raise GraphQLError("Not allowed")

        # Translate relay id to kf_id
        try:
            _, study_id = from_global_id(study)
            study = Study.objects.get(kf_id=study_id)
        except (Study.DoesNotExist):
            raise GraphQLError(f"Study {study_id} does not exist.")

        try:
            _, user_id = from_global_id(user_id)
            collaborator = User.objects.get(id=int(user_id))
        except (User.DoesNotExist, TypeError):
            raise GraphQLError(f"User {user_id} does not exist.")

        try:
            Membership.objects.get(
                study=study, collaborator=collaborator
            ).delete()
        except Membership.DoesNotExist:
            raise GraphQLError(f"User is not a member of the study.")

        # Log an event
        message = (
            f"{user.display_name} removed {collaborator.display_name} "
            f"as collaborator from study {study.kf_id}"
        )
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="CB_REM",
        )
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return RemoveCollaboratorMutation(study=study)


class UpdateSequencingStatusInput(graphene.InputObjectType):
    status = graphene.Field(
        SequencingStatusType, description="The sequencing status of the study"
    )


class UpdateIngestionStatusInput(graphene.InputObjectType):
    status = graphene.Field(
        IngestionStatusType, description="The ingestion status of the study"
    )


class UpdatePhenotypeStatusInput(graphene.InputObjectType):
    status = graphene.Field(
        PhenotypeStatusType, description="The phenotype status of the study",
    )


class UpdateSequencingStatusMutation(graphene.Mutation):
    """ Mutation to change the current sequencing status of a study"""

    class Arguments:
        study = graphene.ID(
            required=True,
            description="The ID of the study to remove the collaborator from",
        )
        data = UpdateSequencingStatusInput(
            required=True,
            description="Input for the study's sequencing status",
        )

    study = graphene.Field(StudyNode)

    def mutate(self, info, study, data):
        """
        Update the sequencing status of a study
        """
        user = info.context.user
        if not user.has_perm("studies.change_sequencing_status"):
            raise GraphQLError("Not allowed")

        # Translate relay id to kf_id
        try:
            _, study_id = from_global_id(study)
            study = Study.objects.get(kf_id=study_id)
        except (Study.DoesNotExist):
            raise GraphQLError(f"Study {study_id} does not exist.")

        # Update the sequencing status on the study
        if "status" in data:
            study.sequencing_status = data["status"]
        study.save()

        # Log an event
        message = (
            f"{user.display_name} study {study.kf_id}'s sequencing status "
            f"to {study.sequencing_status}"
        )
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="ST_UPD",
        )
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return UpdateSequencingStatusMutation(study=study)


class UpdateIngestionStatusMutation(graphene.Mutation):
    """ Mutation to change the current ingestion status of a study"""

    class Arguments:
        study = graphene.ID(
            required=True,
            description="The ID of the study to remove the collaborator from",
        )
        data = UpdateIngestionStatusInput(
            required=True, description="Input for the study's ingestion status"
        )

    study = graphene.Field(StudyNode)

    def mutate(self, info, study, data):
        """
        Update the ingestion status of a study
        """
        user = info.context.user
        if not user.has_perm("studies.change_ingestion_status"):
            raise GraphQLError("Not allowed")

        # Translate relay id to kf_id
        try:
            _, study_id = from_global_id(study)
            study = Study.objects.get(kf_id=study_id)
        except (Study.DoesNotExist):
            raise GraphQLError(f"Study {study_id} does not exist.")

        # Update the ingestion status on the study
        if "status" in data:
            study.ingestion_status = data["status"]
        study.save()

        # Log an event
        message = (
            f"{user.display_name} study {study.kf_id}'s ingestion status "
            f"to {study.ingestion_status}"
        )
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="IN_UPD",
        )
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return UpdateIngestionStatusMutation(study=study)


class UpdatePhenotypeStatusMutation(graphene.Mutation):
    """ Mutation to change the current phenotype status of a study"""

    class Arguments:
        study = graphene.ID(
            required=True,
            description="The ID of the study to remove the collaborator from",
        )
        data = UpdatePhenotypeStatusInput(
            required=True, description="Input for the study's phenotype status"
        )

    study = graphene.Field(StudyNode)

    def mutate(self, info, study, data):
        """
        Update the phenotype status of a study
        """
        user = info.context.user
        if not user.has_perm("studies.change_phenotype_status"):
            raise GraphQLError("Not allowed")

        # Translate relay id to kf_id
        try:
            _, study_id = from_global_id(study)
            study = Study.objects.get(kf_id=study_id)
        except (Study.DoesNotExist):
            raise GraphQLError(f"Study {study_id} does not exist.")

        # Update the phenotype status on the study
        if "status" in data:
            study.phenotype_status = data["status"]
        study.save()

        # Log an event
        message = (
            f"{user.display_name} study {study.kf_id}'s phenotype status "
            f"to {study.phenotype_status}"
        )
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="PH_UPD",
        )
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return UpdatePhenotypeStatusMutation(study=study)


class Mutation:
    """ Mutations for studies """

    create_study = CreateStudyMutation.Field(
        description="""Create a new study including setup in external systems.
        This involves: creating the study in the dataservice, mirroring the
        study in the study-creator api, creating a new bucket for the study
        data, and setting up new projects in Cavatica."""
    )
    update_study = UpdateStudyMutation.Field(
        description="Update a given study"
    )
    add_collaborator = AddCollaboratorMutation.Field(
        description="Add a collaborator to a study"
    )
    remove_collaborator = RemoveCollaboratorMutation.Field(
        description="Add a collaborator to a study"
    )

    update_sequencing_status = UpdateSequencingStatusMutation.Field(
        description="Update the sequencing status of a study"
    )

    update_ingestion_status = UpdateIngestionStatusMutation.Field(
        description="Update the ingestion status of a study"
    )

    update_phenotype_status = UpdatePhenotypeStatusMutation.Field(
        description="Update the phenotype status of a study"
    )
