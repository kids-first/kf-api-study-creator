import graphene
import django_filters
from django.conf import settings
from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_s3_storage.storage import S3Storage
from django_filters import OrderingFilter
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError

from .models import File, Object
from creator.studies.models import Study


class ObjectNode(DjangoObjectType):
    class Meta:
        model = Object
        interfaces = (relay.Node, )


class ObjectFilter(django_filters.FilterSet):
    class Meta:
        model = Object
        fields = []
    order_by = OrderingFilter(fields=('created_at',))


class FileNode(DjangoObjectType):
    class Meta:
        model = File
        interfaces = (relay.Node, )

    versions = DjangoFilterConnectionField(
        ObjectNode,
        filterset_class=ObjectFilter,
    )

    download_url = graphene.String()

    def resolve_download_url(self, info):
        return f'{info.context.scheme}://{info.context.get_host()}{self.path}'


class FileFilter(django_filters.FilterSet):
    class Meta:
        model = File
        fields = ['name', 'study__kf_id', 'file_type']


class UploadMutation(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)
        studyId = graphene.String(required=True)

    success = graphene.Boolean()
    file = graphene.Field(FileNode)

    def mutate(self, info, file, studyId, **kwargs):
        """
            Uploads a file given a studyId and creates a new file and
            file object
        """
        user = info.context.user
        if user is None or not user.is_authenticated:
            raise GraphQLError('Not authenticated to upload a file.')

        if studyId not in user.ego_groups and 'ADMIN' not in user.ego_roles:
            raise GraphQLError('Not authenticated to upload to the study.')

        if file.size > settings.FILE_MAX_SIZE:
            raise GraphQLError('File is too large.')

        study = Study.objects.get(kf_id=studyId)
        new_file = File(name=file.name, study=study)
        new_file.save()
        obj = Object(size=file.size, root_file=new_file, key=file)
        if (settings.DEFAULT_FILE_STORAGE ==
                'django_s3_storage.storage.S3Storage'):
            obj.key.storage = S3Storage(aws_s3_bucket_name=study.bucket)
        obj.save()
        return UploadMutation(success=True, file=new_file)


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
