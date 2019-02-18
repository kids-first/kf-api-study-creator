from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Study 


class StudyNode(DjangoObjectType):
    class Meta:
        model = Study 
        filter_fields = ['name', 'created_at']
        interfaces = (relay.Node, )


class Query(object):
    study = relay.Node.Field(StudyNode)
    all_studies = DjangoFilterConnectionField(StudyNode)
