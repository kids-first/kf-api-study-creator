import graphene
from django.db import transaction
from django.conf import settings
from graphene_file_upload.scalars import Upload
from django_s3_storage.storage import S3Storage
from graphql import GraphQLError
from botocore.exceptions import ClientError

from creator.files.models import File, Version
from creator.studies.models import Study
from creator.events.models import Event
from creator.files.nodes.file import FileNode


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
        study = Study.objects.get(kf_id=studyId)

        if not (
            user.has_perm("files.add_file")
            or (
                user.has_perm("files.add_my_study_file")
                and user.studies.filter(kf_id=study.kf_id).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        if file.size > settings.FILE_MAX_SIZE:
            raise GraphQLError("File is too large.")

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
        if not (
            user.has_perm("files.change_file")
            or user.has_perm("files.change_my_study_file")
        ):
            raise GraphQLError("Not allowed")

        try:
            file = File.objects.get(kf_id=kf_id)
        except File.DoesNotExist:
            raise GraphQLError("File does not exist.")

        if not (
            user.has_perm("files.change_file")
            or (
                user.has_perm("files.change_my_study_file")
                and user.studies.filter(kf_id=file.study.kf_id).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        update_fields = []

        try:
            if kwargs.get("name"):
                if file.name != kwargs.get("name"):
                    update_fields.append("name")
                file.name = kwargs.get("name")
            if kwargs.get("description"):
                if file.description != kwargs.get("description"):
                    update_fields.append("description")
                file.description = kwargs.get("description")
            if kwargs.get("file_type"):
                if file.file_type != kwargs.get("file_type"):
                    update_fields.append("file type")
                file.file_type = kwargs.get("file_type")
            if "tags" in kwargs:
                if file.tags != kwargs.get("tags"):
                    update_fields.append("tags")
                file.tags = kwargs.get("tags")
            file.save()
        except ClientError:
            raise GraphQLError("Failed to save file mutation.")

        # Make an update event
        message = (
            f"{user.username} updated {', '.join(update_fields)} "
            f"{'of ' if len(update_fields)>0 else ''} file {file.kf_id}"
        )
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
        if not user.has_perm("files.delete_file"):
            raise GraphQLError("Not allowed")

        try:
            file = File.objects.get(kf_id=kf_id)
        except File.DoesNotExist:
            raise GraphQLError("File does not exist.")

        file.delete()

        return DeleteFileMutation(success=True, kf_id=kf_id)


class Mutation(graphene.ObjectType):
    create_file = FileUploadMutation.Field(
        description="Upload a new file to a study"
    )
    update_file = FileMutation.Field(description="Update a file")
    delete_file = DeleteFileMutation.Field(description="Delete a file")
