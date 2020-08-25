import graphene
from django.db import transaction
from django.conf import settings
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_relay import from_global_id

from creator.analyses.analyzer import analyze_version
from creator.files.models import File, Version
from creator.studies.models import Study
from creator.events.models import Event
from creator.files.nodes.file import FileNode


class CreateFileMutation(graphene.Mutation):
    class Arguments:
        version = graphene.ID(
            required=True,
            description="The first version this document will contain",
        )
        study = graphene.ID(
            required=False, description="The study this file will belong to"
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

    file = graphene.Field(FileNode)

    def mutate(
        self,
        info,
        version,
        name,
        description,
        fileType,
        tags,
        study=None,
        **kwargs,
    ):
        """
        Creates a new file housing the specified version.
        """
        user = info.context.user

        try:
            _, version_id = from_global_id(version)
            version = Version.objects.get(kf_id=version_id)
        except Version.DoesNotExist:
            raise GraphQLError("Version does not exist.")

        # If there was a study in the mutation, try to resolve it, else try
        # to inherit the study on the version, if there is one, otherwise fail
        # to create a new file
        if study is not None:
            try:
                _, study_id = from_global_id(study)
                study = Study.objects.get(kf_id=study_id)
            except Study.DoesNotExist:
                raise GraphQLError("Study does not exist.")
        else:
            study = version.study
            if study is None:
                raise GraphQLError(
                    "Study must be specified or the version given must have a "
                    "linked study"
                )

        if not (
            user.has_perm("files.add_file")
            or (
                user.has_perm("files.add_my_study_file")
                and user.studies.filter(kf_id=study.kf_id).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        root_file = File(
            name=name,
            study=study,
            creator=user,
            description=description,
            file_type=fileType,
            tags=tags,
        )
        root_file.save()
        version.root_file = root_file
        version.save()

        return CreateFileMutation(file=root_file)


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

        # Make an update event
        message = (
            f"{user.display_name} updated {', '.join(update_fields)} "
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
    create_file = CreateFileMutation.Field(
        description="Upload a new file to a study"
    )
    update_file = FileMutation.Field(description="Update a file")
    delete_file = DeleteFileMutation.Field(description="Delete a file")
