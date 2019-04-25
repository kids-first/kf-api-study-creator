import graphene
import django_filters
from django.conf import settings
from django.db import transaction
from django.db.utils import IntegrityError
from graphene import relay, ObjectType, Field, String
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_s3_storage.storage import S3Storage
from django_filters import OrderingFilter
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError

from botocore.exceptions import ClientError

from .models import File, Object, DownloadToken, DevDownloadToken
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


class DevDownloadTokenNode(DjangoObjectType):
    token = graphene.String()

    class Meta:
        model = DevDownloadToken
        interfaces = (relay.Node, )
        filter_fields = []

    def resolve_token(self, info):
        """
        Return an obscured token with only the first four characters exposed,
        unless the token is being returned in response to a new token mutation.
        """
        if info.path == ['createDevToken', 'token', 'token']:
            return self.token
        return self.token[:4] + '*' * (len(self.token) - 4)


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
        # This extracts the FileFileType enum from the auto-created field
        # made from the django model inside of the FileNode
        file_type = FileNode._meta.fields['file_type'].type

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
        except File.DoesNotExist:
            raise GraphQLError('File does not exist.')

        study_id = file.study.kf_id
        if study_id not in user.ego_groups and 'ADMIN' not in user.ego_roles:
            raise GraphQLError('Not authenticated to mutate a file.')

        try:
            if kwargs.get('name'):
                file.name = kwargs.get('name')
            if kwargs.get('description'):
                file.description = kwargs.get('description')
            if kwargs.get('file_type'):
                file.file_type = kwargs.get('file_type')
            file.save()
        except ClientError as e:
            raise GraphQLError('Failed to save file mutation.')

        return FileMutation(file=file)


class DeleteFileMutation(graphene.Mutation):
    class Arguments:
        kf_id = graphene.String(required=True)

    success = graphene.Boolean()

    def mutate(self, info, kf_id, **kwargs):
        """
        Deletes a file if the user is an admin and the file exists
        """
        user = info.context.user
        if (user is None or
                not user.is_authenticated or
                'ADMIN' not in user.ego_roles):
            raise GraphQLError('Not authenticated to mutate a file.')

        try:
            file = File.objects.get(kf_id=kf_id)
        except File.DoesNotExist:
            raise GraphQLError('File does not exist.')

        file.delete()

        return DeleteFileMutation(success=True)


class SignedUrlMutation(graphene.Mutation):
    """
    Generates a signed url and returns it
    """
    class Arguments:
        study_id = graphene.String(required=True)
        file_id = graphene.String(required=True)
        version_id = graphene.String(required=False)

    url = graphene.String()
    file = graphene.Field(FileNode)

    def mutate(self, info, study_id, file_id, version_id=None, **kwargs):
        """
        Generates a token for a signed url and returns a download url
        with the token inclueded as a url parameter.
        This url will be immediately usable to download the file one time.
        """
        user = info.context.user
        if ((user is None
             or not user.is_authenticated
             or study_id not in user.ego_groups
             and 'ADMIN' not in user.ego_roles)):
            return GraphQLError('Not authenticated to generate a url.')

        try:
            file = File.objects.get(kf_id=file_id)
        except File.DoesNotExist:
            return GraphQLError('No file exists with given ID')
        try:
            if version_id:
                obj = file.versions.get(kf_id=version_id)
            else:
                obj = file.versions.latest('created_at')
        except Object.DoesNotExist:
            return GraphQLError('No version exists with given ID')

        token = DownloadToken(root_object=obj)
        token.save()

        url = f'{obj.path}?token={token.token}'

        return SignedUrlMutation(url=url)


class DevDownloadTokenMutation(graphene.Mutation):
    """
    Generates a developer download token
    """
    class Arguments:
        name = graphene.String(required=True)

    token = graphene.Field(DevDownloadTokenNode)

    def mutate(self, info, name, **kwargs):
        """
        Generates a developer token with a given name.
        """
        user = info.context.user
        if ((user is None
             or not user.is_authenticated
             or 'ADMIN' not in user.ego_roles)):
            return GraphQLError('Not authenticated to generate a token.')

        token = DevDownloadToken(name=name)
        try:
            token.save()
        except IntegrityError:
            return GraphQLError("Token with this name already exists.")

        return DevDownloadTokenMutation(token=token)


class DeleteDevDownloadTokenMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    success = graphene.Boolean()
    name = graphene.String()

    def mutate(self, info, name, **kwargs):
        """
        Deletes a developer download token by name
        """
        user = info.context.user
        if (user is None or
                not user.is_authenticated or
                'ADMIN' not in user.ego_roles):
            raise GraphQLError('Not authenticated to delete a token.')

        try:
            token = DevDownloadToken.objects.get(name=name)
        except DevDownloadToken.DoesNotExist:
            raise GraphQLError('Token does not exist.')

        token.delete()

        return DeleteDevDownloadTokenMutation(success=True, name=token.name)


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

    all_dev_tokens = DjangoFilterConnectionField(DevDownloadTokenNode)

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

    def resolve_all_dev_tokens(self, info, **kwargs):
        """
        If user is admin, return all tokens, otherwise return none
        """
        user = info.context.user

        if user is None or not user.is_authenticated:
            return DevDownloadToken.objects.none()

        if user.is_admin:
            return DevDownloadToken.objects.all()

        return DevDownloadToken.objects.none()
