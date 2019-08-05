import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from graphql import GraphQLError
from graphene import (
    relay,
    Boolean,
    InputObjectType,
    ObjectType,
    Field,
    String,
    Mutation,
)
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Study, Batch


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
    name = String()
    visible = Boolean()

    attribution = String()
    data_access_authority = String()
    external_id = String(required=False)
    release_status = String()
    short_name = String()
    version = String()


class CreateStudyMutation(Mutation):
    class Arguments:
        input = StudyInput(required=True)

    study = Field(StudyNode)

    def mutate(self, info, **kwargs):
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

        try:
            resp = requests.post(
                f"{settings.DATASERVICE_URL}/studies",
                json=kwargs["input"],
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

        return CreateStudyMutation(study=study)


class BatchNode(DjangoObjectType):
    class Meta:
        model = Batch
        filter_fields = ['name', 'state']
        interfaces = (relay.Node, )


class Query(object):
    study = relay.Node.Field(StudyNode)
    study_by_kf_id = Field(StudyNode, kf_id=String(required=True))
    all_studies = DjangoFilterConnectionField(StudyNode)

    batch = relay.Node.Field(BatchNode)
    all_batches = DjangoFilterConnectionField(BatchNode)

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
