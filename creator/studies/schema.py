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
    all_batches  = DjangoFilterConnectionField(BatchNode)
