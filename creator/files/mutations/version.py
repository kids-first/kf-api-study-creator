import graphene
from django.conf import settings
from django.db import transaction
from django_s3_storage.storage import S3Storage
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_relay import from_global_id
from botocore.exceptions import ClientError

from creator.analyses.analyzer import analyze_version
from creator.studies.models import Study
from creator.files.models import File, Version
from creator.files.nodes.version import VersionNode


class VersionMutation(graphene.Mutation):
    """
    Updates fields for a given version.
    """

    class Arguments:
        kf_id = graphene.String(required=True)
        description = graphene.String()
        # This extracts the VersionState enum from the auto-created field
        # made from the django model inside of the VersionNode
        state = VersionNode._meta.fields["state"].type

    version = graphene.Field(VersionNode)

    def mutate(self, info, kf_id, **kwargs):
        """
        Updates an existing version of a file.
        User must be authenticated and belongs to the study, or be ADMIN.
        """
        user = info.context.user

        if not (
            user.has_perm("files.change_version_meta")
            or user.has_perm("files.change_my_version_meta")
            or user.has_perm("files.change_version_status")
            or user.has_perm("files.change_my_version_status")
        ):
            raise GraphQLError("Not allowed")

        try:
            version = Version.objects.get(kf_id=kf_id)
        except Version.DoesNotExist:
            raise GraphQLError("Version does not exist.")

        study_id = version.root_file.study.kf_id

        try:
            if kwargs.get("description"):
                if kwargs.get("description") != version.description and (
                    not (
                        user.has_perm("files.change_version_meta")
                        or (
                            user.has_perm("files.change_my_version_meta")
                            and user.studies.filter(kf_id=study_id).exists()
                        )
                    )
                ):
                    raise GraphQLError("Not allowed")
                version.description = kwargs.get("description")
            if kwargs.get("state"):
                if kwargs.get("state") != version.state and (
                    not (
                        user.has_perm("files.change_version_status")
                        or (
                            user.has_perm("files.change_my_version_status")
                            and user.studies.filter(kf_id=study_id).exists()
                        )
                    )
                ):
                    raise GraphQLError("Not allowed")
                version.state = kwargs.get("state")
            version.save()
        except ClientError:
            raise GraphQLError("Failed to save version mutation.")

        return VersionMutation(version=version)


class VersionUploadMutation(graphene.Mutation):
    class Arguments:
        file = Upload(
            required=True,
            description="Empty argument used by the multipart request",
        )
        fileId = graphene.String(
            required=False,
            description="kf_id of the file this version will belong to",
        )
        study = graphene.ID(
            required=False, description="The study this version will belong to"
        )
        description = graphene.String(
            required=False,
            description=(
                "A description of the changes made in this version to"
                " the file"
            ),
        )

    success = graphene.Boolean()
    version = graphene.Field(VersionNode)

    def mutate(
        self, info, file, fileId=None, study=None, description=None, **kwargs
    ):
        """
        Uploads a new version of a file given a fileId or study.
        A user may upload a version knowing what existing file it will augment,
        or they may upload the version before it is known (in the case of an
        entirely new file) but they must at least specify the study they are
        uploading to for the purpose of permissions and knowing where the file
        must reside in S3.
        """
        user = info.context.user

        root_file = None

        if fileId is None and study is None:
            raise GraphQLError("Either a file or study must be specified")

        if fileId:
            # Try to look up the file, if specified
            try:
                root_file = File.objects.get(kf_id=fileId)
            except File.DoesNotExist:
                raise GraphQLError("File does not exist.")

            study = root_file.study
        else:
            _, kf_id = from_global_id(study)
            study = Study.objects.get(kf_id=kf_id)

        # Make sure user is allowed to upload to this study
        if not (
            user.has_perm("files.add_version")
            or (
                user.has_perm("files.add_my_study_version")
                and user.studies.filter(kf_id=study.kf_id).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        if file.size > settings.FILE_MAX_SIZE:
            raise GraphQLError("File is too large.")

        try:
            with transaction.atomic():
                version = Version(
                    file_name=file.name,
                    size=file.size,
                    root_file=root_file,
                    study=study,
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

        if user.has_perm("analyses.add_analysis") or (
            user.has_perm("analysis.add_my_study_analysis")
            and user.studies.filter(kf_id=study.kf_id).exists()
        ):
            analysis = analyze_version(version)
            analysis.creator = user
            analysis.save()

        return VersionUploadMutation(success=True, version=version)


class Mutation(graphene.ObjectType):
    create_version = VersionUploadMutation.Field(
        description="Upload a new version of a file"
    )
    update_version = VersionMutation.Field(description="Update a file version")
