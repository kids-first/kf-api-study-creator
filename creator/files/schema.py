from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import FileEssence, Object


class FileNode(DjangoObjectType):
    class Meta:
        model = FileEssence
        filter_fields = ['name', 'study__name', 'study__kf_id']
        interfaces = (relay.Node, )


class ObjectNode(DjangoObjectType):
    class Meta:
        model = Object
        filter_fields = ['bucket', 'key', 'version_id']
        interfaces = (relay.Node, )


class Query(object):
    file_essence = relay.Node.Field(FileNode)
    study_files = DjangoFilterConnectionField(FileNode)
    all_files = DjangoFilterConnectionField(FileNode)

    file_version = relay.Node.Field(ObjectNode)
    all_versions = DjangoFilterConnectionField(ObjectNode)
