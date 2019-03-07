from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from graphene import relay, ObjectType, Field, String
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
