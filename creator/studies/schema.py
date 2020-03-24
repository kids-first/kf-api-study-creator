import django_rq
import json
import logging
import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from graphql import GraphQLError
from graphql_relay import from_global_id
from graphene import (
    relay,
    List,
    Boolean,
    Date,
    InputObjectType,
    ID,
    List,
    ObjectType,
    Field,
    String,
    Int,
    Mutation,
)
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from dateutil.parser import parse
from .models import Study
from creator.tasks import setup_bucket_task
from creator.tasks import setup_cavatica_task
from creator.events.models import Event
from creator.events.schema import EventNode, EventFilter
from creator.files.models import File
from creator.files.schema.file import FileNode, FileFilter

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


class StudyNode(DjangoObjectType):
    """ A study in Kids First """

    events = DjangoFilterConnectionField(
        EventNode, filterset_class=EventFilter, description="List all events"
    )

    files = DjangoFilterConnectionField(
        FileNode, filterset_class=FileFilter, description="List all files"
    )

    class Meta:
        model = Study
        filter_fields = ["name"]
        exclude_fields = ["user_set"]
        interfaces = (relay.Node,)

    @classmethod
    def get_node(cls, info, kf_id):
        """
        Only return node if user is an admin or is in the study group
        """
        try:
            study = cls._meta.model.objects.get(kf_id=kf_id)
        except cls._meta.model.DoesNotExist:
            return None

        user = info.context.user
        if user.has_perm("studies.view_study") or (
            user.has_perm("studies.view_my_study")
            and user.studies.filter(kf_id=study.kf_id).exists()
        ):
            return study
        else:
            raise GraphQLError("Not allowed")


class StudyInput(InputObjectType):
    # These fields are from the study model in dataservice
    name = String(description="The full name of the study")
    visible = Boolean(
        description="Whether or not the study is visible in the dataservice"
    )

    attribution = String(
        description="URL providing more information about the study"
    )
    data_access_authority = String(
        description="The organization that moderates access to the study"
    )
    external_id = String(
        required=False,
        description=(
            "The primary identifier this study is know by outside of "
            "Kids-First, often the dbGaP phsid."
        ),
    )
    release_status = String(
        description="Release status as set in the dataservice"
    )
    short_name = String(
        description=(
            "Short name of the study for use in space-restricted containers"
        )
    )
    version = String(
        description=(
            "Study version, often the provided by the data access authority"
        )
    )

    # These fields are unique to study-creator
    description = String(
        description="Study description, often a grant abstract"
    )
    anticipated_samples = Int(
        description="Number of expected samples for this study"
    )
    awardee_organization = String(
        description="Organization associated with the X01 grant"
    )
    release_date = Date(
        description=(
            "Date that this study is expected to be released to the public"
        )
    )
    bucket = String(
        description="The s3 bucket where data for this study resides"
    )


class CreateStudyInput(StudyInput):
    collaborators = List(
        ID,
        description=(
            "Users related to the study. "
            "If null, the collaborators will not be modified."
        ),
    )


class CreateStudyMutation(Mutation):
    class Arguments:
        input = CreateStudyInput(
            required=True, description="Attributes for the new study"
        )
        workflows = List(
            String,
            description="Workflows to be run for this study",
            required=False,
        )

    study = Field(StudyNode)

    def mutate(self, info, input, workflows=None):
        """
        Creates a new study.
        If FEAT_DATASERVICE_CREATE_STUDIES is enabled, try to first create
        the study in the dataservice. If the request fails, no study will be
        saved in the creator's database
        If FEAT_DATASERVICE_CREATE_STUDIES is not enabled, we will still
        create the study, but it will be labeled as a local study.
        """
        user = info.context.user
        if (
            user is None
            or not user.is_authenticated
            or "ADMIN" not in user.ego_roles
        ):
            raise GraphQLError("Not authenticated to create a study.")

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

        # Merge dataservice response attributes with the original input
        attributes = {**input, **resp.json()["results"]}
        created_at = attributes.get("created_at")
        if created_at:
            attributes["created_at"] = parse(created_at)
        attributes["deleted"] = False
        study = Study(**attributes)
        study.save()
        study.collaborators.set(collaborators)
        study.save()

        # Log an event
        message = f"{user.username} created study {study.kf_id}"
        event = Event(study=study, description=message, event_type="SD_CRE")
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

        return CreateStudyMutation(study=study)


class UpdateStudyMutation(Mutation):
    class Arguments:
        id = ID(required=True, description="The ID of the study to update")
        input = StudyInput(
            required=True, description="Attributes for the new study"
        )

    study = Field(StudyNode)

    def mutate(self, info, id, input):
        """
        Updates an existing study
        If FEAT_DATASERVICE_UPDATE_STUDIES is enabled, try to first update
        the study in the dataservice. If the request fails, no study will be
        updated in the creator's database
        """
        user = info.context.user
        if (
            user is None
            or not user.is_authenticated
            or "ADMIN" not in user.ego_roles
        ):
            raise GraphQLError("Not authenticated to update a study.")

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
        message = f"{user.username} updated study {study.kf_id}"
        event = Event(study=study, description=message, event_type="SD_UPD")
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return CreateStudyMutation(study=study)


class AddCollaboratorMutation(Mutation):
    class Arguments:
        study = ID(
            required=True,
            description="The ID of the study to add the collaborator to",
        )
        user = ID(
            required=True,
            description="The ID of the user to add the to the study",
        )

    study = Field(StudyNode)

    def mutate(self, info, study, user):
        """
        Add a user as a collaborator to a study
        """
        user_id = user
        user = info.context.user
        if (
            user is None
            or not user.is_authenticated
            or "ADMIN" not in user.ego_roles
        ):
            raise GraphQLError("Not authenticated to add a user to a study.")

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

        study.collaborators.add(collaborator)
        study.save()

        # Log an event
        message = (
            f"{user.username} added as collaborator to study {study.kf_id}"
        )
        event = Event(study=study, description=message, event_type="CB_ADD")
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return AddCollaboratorMutation(study=study)


class RemoveCollaboratorMutation(Mutation):
    class Arguments:
        study = ID(
            required=True,
            description="The ID of the study to remove the collaborator from",
        )
        user = ID(
            required=True,
            description="The ID of the user to remove from the study",
        )

    study = Field(StudyNode)

    def mutate(self, info, study, user):
        """
        Remove a user as a collaborator to a study
        """
        user_id = user
        user = info.context.user
        if (
            user is None
            or not user.is_authenticated
            or "ADMIN" not in user.ego_roles
        ):
            raise GraphQLError(
                "Not authenticated to remove a user from a study."
            )

        # Translate relay id to kf_id
        try:
            _, study_id = from_global_id(study)
            study = Study.objects.get(kf_id=study_id)
        except (Study.DoesNotExist):
            raise GraphQLError(f"Study {study_id} does not exist.")

        try:
            _, user_id = from_global_id(user_id)
            user = User.objects.get(id=int(user_id))
        except (User.DoesNotExist, TypeError):
            raise GraphQLError(f"User {user_id} does not exist.")

        study.collaborators.remove(user)
        study.save()

        # Log an event
        message = (
            f"{user.username} removed as collaborator from study {study.kf_id}"
        )
        event = Event(study=study, description=message, event_type="CB_REM")
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return RemoveCollaboratorMutation(study=study)


class Query(object):
    study = relay.Node.Field(StudyNode, description="Get a study")
    study_by_kf_id = Field(
        StudyNode,
        kf_id=String(required=True),
        description="Get a study by its kf_id",
    )
    all_studies = DjangoFilterConnectionField(
        StudyNode, description="List all studies"
    )

    def resolve_study_by_kf_id(self, info, kf_id):
        return StudyNode.get_node(info, kf_id)

    def resolve_all_studies(self, info, **kwargs):
        """
        If user is USER, only return the studies which the user belongs to
        If user is ADMIN, return all studies
        If user is unauthed, return no studies
        """
        user = info.context.user

        if user.has_perm("studies.view_study"):
            return Study.objects.filter(deleted=False).all()

        if user.has_perm("studies.view_my_study"):
            return user.studies.filter(deleted=False).all()

        raise GraphQLError("Not allowed")
