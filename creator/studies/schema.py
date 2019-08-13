import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from graphql import GraphQLError
from graphql_relay import from_global_id
from graphene import (
    relay,
    Boolean,
    InputObjectType,
    ID,
    ObjectType,
    Field,
    String,
    Int,
    Mutation,
)
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Study
from creator.projects.cavatica import setup_cavatica
from creator.events.models import Event


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


class StudyNode(DjangoObjectType):
    class Meta:
        model = Study
        filter_fields = ['name']
        interfaces = (relay.Node, )

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

        if not user.is_authenticated:
            return None

        if user.is_admin:
            return study

        if study.kf_id in user.ego_groups:
            return study

        return None


class StudyInput(InputObjectType):
    # These fields are from the study model in dataservice
    name = String()
    visible = Boolean()

    attribution = String()
    data_access_authority = String()
    external_id = String(required=False)
    release_status = String()
    short_name = String()
    version = String()

    # These fields are unique to study-creator
    description = String()
    anticipated_samples = Int()
    awardee_organization = String()


class CreateStudyMutation(Mutation):
    class Arguments:
        input = StudyInput(required=True)

    study = Field(StudyNode)

    def mutate(self, info, input):
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
        try:
            resp = requests.post(
                f"{settings.DATASERVICE_URL}/studies",
                json=attributes,
                timeout=settings.REQUESTS_TIMEOUT,
                headers=settings.REQUESTS_HEADERS,
            )
        except requests.exceptions.RequestException as e:
            raise GraphQLError(f"Problem creating study: {e}")

        # Raise an error if it looks like study failed to create
        if not resp.status_code == 201 or "results" not in resp.json():
            error = resp.json()
            if "_status" in error:
                error = error["_status"]
            if "message" in error:
                error = error["message"]
            raise GraphQLError(f"Problem creating study: {error}")

        attributes = resp.json()["results"]
        study = Study(**attributes)
        study.save()

        if (
            settings.FEAT_CAVATICA_CREATE_PROJECTS
            and settings.CAVATICA_URL
            and settings.CAVATICA_HARMONIZATION_TOKEN
            and settings.CAVATICA_DELIVERY_TOKEN
        ):
            setup_cavatica(study)

        # Log an event
        message = f"{user.username} created created study {study.kf_id}"
        event = Event(study=study, description=message, event_type="SD_CRE")
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return CreateStudyMutation(study=study)


class UpdateStudyMutation(Mutation):
    class Arguments:
        id = ID(required=True)
        input = StudyInput(required=True)

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
        # ensure we are completely in-sync
        attributes = resp.json()["results"]
        study = Study(**attributes)
        study.save()

        # Log an event
        message = f"{user.username} created updated study {study.kf_id}"
        event = Event(study=study, description=message, event_type="SD_UPD")
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return CreateStudyMutation(study=study)


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

        if not user.is_authenticated or user is None:
            return Study.objects.none()

        if user.is_admin:
            return Study.objects.all()

        return Study.objects.filter(kf_id__in=user.ego_groups)
