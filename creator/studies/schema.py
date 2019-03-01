from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Study, Batch


class StudyNode(DjangoObjectType):
    class Meta:
        model = Study
        filter_fields = ['name']
        interfaces = (relay.Node, )


class BatchNode(DjangoObjectType):
    class Meta:
        model = Batch
        filter_fields = ['name', 'state']
        interfaces = (relay.Node, )


class Query(object):
    study = relay.Node.Field(StudyNode)
    all_studies = DjangoFilterConnectionField(StudyNode)

    batch = relay.Node.Field(BatchNode)
    all_batches = DjangoFilterConnectionField(BatchNode)

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
