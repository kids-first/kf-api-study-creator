import graphene
import django_filters
from django.conf import settings
from django.db import transaction
from graphene import relay, ObjectType, Field, String
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_s3_storage.storage import S3Storage
from django_filters import OrderingFilter
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError

from botocore.exceptions import ClientError

from .models import File, Object
from creator.studies.models import Study


class ObjectNode(DjangoObjectType):
    class Meta:
        model = Object
        interfaces = (relay.Node, )

    download_url = graphene.String()

    def resolve_download_url(self, info):
        return f'{info.context.scheme}://{info.context.get_host()}{self.path}'

    @classmethod
    def get_node(cls, info, kf_id):
        """
        Only return node if user is an admin or is in the study group
        """
        try:
            obj = cls._meta.model.objects.get(kf_id=kf_id)
        except cls._meta.model.DoesNotExist:
            return None

        user = info.context.user

        if not user.is_authenticated:
            return None

        if user.is_admin:
            return obj

        if obj.root_file.study.kf_id in user.ego_groups:
            return obj

        return None


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

    @classmethod
    def get_node(cls, info, kf_id):
        """
        Only return node if user is an admin or is in the study group
        """
        try:
            file = cls._meta.model.objects.get(kf_id=kf_id)
        except cls._meta.model.DoesNotExist:
            return None

        user = info.context.user

        if not user.is_authenticated:
            return None

        if user.is_admin:
            return file

        if file.study.kf_id in user.ego_groups:
            return file

        return None


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
        try:
            with transaction.atomic():
                new_file = File(name=file.name, study=study)
                new_file.save()
                obj = Object(size=file.size, root_file=new_file, key=file)
                if (settings.DEFAULT_FILE_STORAGE ==
                        'django_s3_storage.storage.S3Storage'):
                    obj.key.storage = S3Storage(
                        aws_s3_bucket_name=study.bucket
                    )
                obj.save()
        except ClientError as e:
            raise GraphQLError('Failed to save file')

        return UploadMutation(success=True, file=new_file)


class FileMutation(graphene.Mutation):
    class Arguments:
        kf_id = graphene.String(required=True)
        name = graphene.String()
        description = graphene.String()

    file = graphene.Field(FileNode)

    def mutate(self, info, kf_id, **kwargs):
        """
            Updates an existing file on name and/or description.
            User must be authenticated and belongs to the study, or be ADMIN.
        """
        user = info.context.user
        if user is None or not user.is_authenticated:
            raise GraphQLError('Not authenticated to mutate a file.')

        try:
            file = File.objects.get(kf_id=kf_id)
        except:
            raise GraphQLError('File does not exist.')

        study_id = file.study.kf_id
        if study_id not in user.ego_groups and 'ADMIN' not in user.ego_roles:
            raise GraphQLError('Not authenticated to mutate a file.')

        try:
            if kwargs.get('name'):
                file.name = kwargs.get('name')
            if kwargs.get('description'):
                file.description = kwargs.get('description')
            file.save()
        except ClientError as e:
            raise GraphQLError('Failed to save file mutation.')

        return FileMutation(file=file)


class Query(object):
    file = relay.Node.Field(FileNode)
    file_by_kf_id = Field(FileNode, kf_id=String(required=True))
    all_files = DjangoFilterConnectionField(
        FileNode,
        filterset_class=FileFilter,
    )

    version = relay.Node.Field(ObjectNode)
    version_by_kf_id = Field(ObjectNode, kf_id=String(required=True))
    all_versions = DjangoFilterConnectionField(
        ObjectNode,
        filterset_class=ObjectFilter,
    )

    def resolve_file_by_kf_id(self, info, kf_id):
        return FileNode.get_node(info, kf_id)

    def resolve_version_by_kf_id(self, info, kf_id):
        return ObjectNode.get_node(info, kf_id)

    def resolve_all_files(self, info, **kwargs):
        """
        If user is USER, only return the files from the studies
        which the user belongs to
        If user is ADMIN, return all files
        If user is unauthed, return no files
        """
        user = info.context.user

        if not user.is_authenticated or user is None:
            return File.objects.none()

        if user.is_admin:
            return File.objects.all()

        return File.objects.filter(study__kf_id__in=user.ego_groups)

    def resolve_all_versions(self, info, **kwargs):
        """
        If user is USER, only return the file versions from the studies
        which the user belongs to
        If user is ADMIN, return all file versions
        If user is unauthed, return no file versions
        """
        user = info.context.user

        if not user.is_authenticated or user is None:
            return Object.objects.none()

        if user.is_admin:
            return Object.objects.all()

        return Object.objects.filter(
            root_file__study__kf_id__in=user.ego_groups
        )
