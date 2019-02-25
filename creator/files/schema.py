import graphene
import django_filters
from django.conf import settings
from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_s3_storage.storage import S3Storage
from django_filters import OrderingFilter

from .models import File, Object

from graphene_file_upload.scalars import Upload

from creator.studies.models import Study


class UploadMutation(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)
        studyId = graphene.String(required=True)

    success = graphene.Boolean()

    def mutate(self, info, file, studyId, **kwargs):
        """
            Uploads a file given a studyId and creates a new file and
            file object
        """
        study = Study.objects.get(kf_id=studyId)
        new_file = File(name=file.name, study=study)
        new_file.save()
        obj = Object(size=file.size, root_file=new_file, key=file)
        if (settings.DEFAULT_FILE_STORAGE ==
                'django_s3_storage.storage.S3Storage'):
            obj.key.storage = S3Storage(aws_s3_bucket_name=study.bucket)
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
        model = File
        fields = ['name', 'study__kf_id', 'file_type']


class FileNode(DjangoObjectType):
    class Meta:
        model = File
        interfaces = (relay.Node, )

    versions = DjangoFilterConnectionField(
        ObjectNode,
        filterset_class=ObjectFilter,
    )


class Query(object):
    file = relay.Node.Field(FileNode)
    all_files = DjangoFilterConnectionField(
        FileNode,
        filterset_class=FileFilter,
    )

    all_versions = DjangoFilterConnectionField(
        ObjectNode,
        filterset_class=ObjectFilter,
    )
