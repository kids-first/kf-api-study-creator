import graphene
import django_filters
from django.conf import settings
from django.db import transaction
from graphene import relay, Field, String
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_s3_storage.storage import S3Storage
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from .version import VersionNode, VersionFilter

from botocore.exceptions import ClientError

from ..models import File, Version
from creator.studies.models import Study
from creator.events.models import Event


class FileNode(DjangoObjectType):
    class Meta:
        model = File
        interfaces = (relay.Node,)

    versions = DjangoFilterConnectionField(
        VersionNode, filterset_class=VersionFilter
    )

    download_url = graphene.String()

    def resolve_download_url(self, info):
        return f"{info.context.scheme}://{info.context.get_host()}{self.path}"

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
    tag = django_filters.CharFilter(field_name="tags", lookup_expr="icontains")

    class Meta:
        model = File
        fields = ["name", "study__kf_id", "file_type"]


class FileUploadMutation(graphene.Mutation):
    class Arguments:
        file = Upload(
            required=True,
            description="Empty argument used by the multipart request",
        )
        studyId = graphene.String(
            required=True,
            description="kf_id of the study this file will belong to",
        )
        name = graphene.String(
            required=True, description="The name of the file"
        )
        description = graphene.String(
            required=True, description="A description of this file"
        )
        # This extracts the FileFileType enum from the auto-created field
        # made from the django model inside of the FileNode
        fileType = FileNode._meta.fields["file_type"].type
        tags = graphene.List(graphene.String)

    success = graphene.Boolean()
    file = graphene.Field(FileNode)

    def mutate(
        self, info, file, studyId, name, description, fileType, tags, **kwargs
    ):
        """
        Uploads a file given a studyId and creates a new file and file version
        if the file does not exist.
        """
        user = info.context.user
        if user is None or not user.is_authenticated:
            raise GraphQLError("Not authenticated to upload a file.")

        if studyId not in user.ego_groups and "ADMIN" not in user.ego_roles:
            raise GraphQLError("Not authenticated to upload to the study.")

        if file.size > settings.FILE_MAX_SIZE:
            raise GraphQLError("File is too large.")

        study = Study.objects.get(kf_id=studyId)

        try:
            # We will do this in a transaction so that if something fails, we
            # can be assured that neither the file nor the version get saved
            with transaction.atomic():
                # First create the file
                root_file = File(
                    name=name,
                    study=study,
                    creator=user,
                    description=description,
                    file_type=fileType,
                    tags=tags,
                )
                root_file.save()
                # Now create the version
                version = Version(
                    file_name=file.name,
                    size=file.size,
                    root_file=root_file,
                    key=file,
                    creator=user,
                    description=description,
                )
                if (
                    settings.DEFAULT_FILE_STORAGE
                    == "django_s3_storage.storage.S3Storage"
                ):
                    version.key.storage = S3Storage(
                        aws_s3_bucket_name=study.bucket
                    )
                version.save()
        except ClientError:
            raise GraphQLError("Failed to save file")

        return FileUploadMutation(success=True, file=root_file)


class FileMutation(graphene.Mutation):
    class Arguments:
        kf_id = graphene.String(required=True)
        name = graphene.String()
        description = graphene.String()
        # This extracts the FileFileType enum from the auto-created field
        # made from the django model inside of the FileNode
        file_type = FileNode._meta.fields["file_type"].type
        tags = graphene.List(graphene.String)

    file = graphene.Field(FileNode)

    def mutate(self, info, kf_id, **kwargs):
        """
            Updates an existing file on name and/or description.
            User must be authenticated and belongs to the study, or be ADMIN.
        """
        user = info.context.user
        if user is None or not user.is_authenticated:
            raise GraphQLError("Not authenticated to mutate a file.")

        try:
            file = File.objects.get(kf_id=kf_id)
        except File.DoesNotExist:
            raise GraphQLError("File does not exist.")

        study_id = file.study.kf_id
        if study_id not in user.ego_groups and "ADMIN" not in user.ego_roles:
            raise GraphQLError("Not authenticated to mutate a file.")

        try:
            if kwargs.get("name"):
                file.name = kwargs.get("name")
            if kwargs.get("description"):
                file.description = kwargs.get("description")
            if kwargs.get("file_type"):
                file.file_type = kwargs.get("file_type")
            if kwargs.get("tags"):
                file.tags = kwargs.get("tags")
            file.save()
        except ClientError:
            raise GraphQLError("Failed to save file mutation.")

        # Make an update event
        message = f"{user.username} updated file {file.kf_id}"
        event = Event(
            file=file,
            study=file.study,
            user=user,
            description=message,
            event_type="SF_UPD",
        )
        event.save()

        return FileMutation(file=file)


class DeleteFileMutation(graphene.Mutation):
    class Arguments:
        kf_id = graphene.String(required=True)

    success = graphene.Boolean()
    kf_id = graphene.String()

    def mutate(self, info, kf_id, **kwargs):
        """
        Deletes a file if the user is an admin and the file exists
        """
        user = info.context.user
        if (
            user is None
            or not user.is_authenticated
            or "ADMIN" not in user.ego_roles
        ):
            raise GraphQLError("Not authenticated to mutate a file.")

        try:
            file = File.objects.get(kf_id=kf_id)
        except File.DoesNotExist:
            raise GraphQLError("File does not exist.")

        file.delete()

        return DeleteFileMutation(success=True, kf_id=kf_id)


class FileQuery:
    file = relay.Node.Field(FileNode, description="Get a file")
    file_by_kf_id = Field(
        FileNode,
        kf_id=String(required=True),
        description="Get a file by its kf_id",
    )
    all_files = DjangoFilterConnectionField(
        FileNode, filterset_class=FileFilter, description="List all files"
    )

    def resolve_file_by_kf_id(self, info, kf_id):
        return FileNode.get_node(info, kf_id)

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
