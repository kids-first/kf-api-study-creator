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
)
from django_filters import FilterSet, OrderingFilter
from graphene_django.filter import DjangoFilterConnectionField
from dateutil.parser import parse
from .models import Study
from creator.studies.nodes import StudyNode
from creator.studies.mutations import Mutation

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class StudyFilter(FilterSet):
    order_by = OrderingFilter(
        fields=("name", "created_at", "organization", "versions__created_at")
    )

    class Meta:
        model = Study
        fields = ["name", "organization"]


class Query(object):
    study = relay.Node.Field(StudyNode, description="Get a study")
    study_by_kf_id = Field(
        StudyNode,
        kf_id=String(required=True),
        description="Get a study by its kf_id",
    )
    all_studies = DjangoFilterConnectionField(
        StudyNode, description="List all studies", filterset_class=StudyFilter
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
