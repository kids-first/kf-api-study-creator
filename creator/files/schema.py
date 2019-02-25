import graphene
import django_filters
from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import OrderingFilter

from .models import FileEssence, Object

from graphene_file_upload.scalars import Upload

from creator.studies.models import Study


class UploadMutation(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)
        studyId = graphene.String(required=True)

    success = graphene.Boolean()

    def mutate(self, info, file, studyId, **kwargs):
        """
            Uploads a file given a studyId and creates a new file essence and
            file object
        """
        study = Study.objects.get(kf_id=studyId)
        file_ess = FileEssence(name=file.name, study=study)
        file_ess.save()
        obj = Object(size=file.size, root_file=file_ess, key=file)
        obj.save()
        return UploadMutation(success=True)


class ObjectFilter(django_filters.FilterSet):
    class Meta:
        model = Object
        fields = []
    order_by = OrderingFilter(fields=('created_at',))


class ObjectNode(DjangoObjectType):
    class Meta:
        model = Object
        interfaces = (relay.Node, )


class FileFilter(django_filters.FilterSet):
    class Meta:
        model = FileEssence
        fields = ['name', 'study__kf_id', 'file_type']


class FileNode(DjangoObjectType):
    class Meta:
        model = FileEssence
        interfaces = (relay.Node, )

    versions = DjangoFilterConnectionField(
        ObjectNode,
        filterset_class=ObjectFilter,
    )


class Query(object):
    file_essence = relay.Node.Field(FileNode)
    all_files = DjangoFilterConnectionField(
        FileNode,
        filterset_class=FileFilter,
    )

    all_versions = DjangoFilterConnectionField(
        ObjectNode,
        filterset_class=ObjectFilter,
    )
