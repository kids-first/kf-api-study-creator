import logging
import graphene
import uuid
import django_rq
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
from creator.files.object_types import TemplateMatchResult
from creator.data_templates.nodes.template_version import TemplateVersionNode
from creator.data_templates.models import TemplateVersion
from creator.files.utils import evaluate_template_match
from creator.files.tasks import (
    is_file_upload_manifest,
    push_to_dewrangle
)

logger = logging.getLogger(__name__)


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
        file = graphene.ID(required=False)

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

        if version.study is not None:
            study_id = version.study.kf_id
        elif version.root_file is not None:
            study_id = version.root_file.study.kf_id
        else:
            raise GraphQLError("Version must be part of a study.")

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

            if kwargs.get("file"):
                if version.root_file is None and (
                    not (
                        user.has_perm("files.change_version_meta")
                        or (
                            user.has_perm("files.change_my_version_meta")
                            and user.studies.filter(kf_id=study_id).exists()
                        )
                    )
                ):
                    raise GraphQLError("Not allowed")

                file_id = kwargs.get("file")
                _, kf_id = from_global_id(file_id)
                try:
                    file = File.objects.get(kf_id=kf_id)
                except File.DoesNotExist:
                    raise GraphQLError("File does not exist.")
                version.root_file = file

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
                # Manually prepend the version uuid to the file name to prevent
                # accidental overwrites of other files in the same storage
                # location. Django will do this for us with the file storage
                # backend, but we disable this feature for S3 storage to allow
                # us to overwrite files when needed.
                file_uuid = uuid.uuid4()
                file_name = file.name
                file.name = f"{file_uuid}_{file.name}"
                version = Version(
                    uuid=file_uuid,
                    file_name=file_name,
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
            user.has_perm("analyses.add_my_study_analysis")
            and user.studies.filter(kf_id=study.kf_id).exists()
        ):
            analysis = analyze_version(version)
            analysis.creator = user
            analysis.save()

        if (
            settings.FEAT_DEWRANGLE_INTEGRATION and
            is_file_upload_manifest(version)
        ):
            logger.info(
                f"Queued version {version.kf_id} {version.root_file.name} for"
                " audit processing..."
            )
            push_to_dewrangle(version.pk)
            # django_rq.enqueue(
            #     push_to_dewrangle, version_id=version.pk
            # )

        return VersionUploadMutation(success=True, version=version)


class EvaluateTemplateMatchInput(graphene.InputObjectType):
    """Parameters used when validating a file version against templates"""

    file_version = graphene.ID(
        required=True, description="The file version being validated"
    )
    study = graphene.ID(
        required=True,
        description="The study which the file version belongs to"
    )


class EvaluateTemplateMatchMutation(graphene.Mutation):
    """
    Evaluate a file version against the templates in the study that the
    file belongs to. For each template, report the details of the mismatch
    between the file's columns and the template's required and optional
    columns.

    See creator.files.utils.evaluate_template_match for details on the match
    evaluation
    """
    class Arguments:
        input = EvaluateTemplateMatchInput(
            required=True,
            description="Attributes for the mutation",
        )

    results = graphene.List(TemplateMatchResult)

    def mutate(self, info, input):
        """
        Evaluate a file version against the templates in the study that the
        file belongs to. See creator.files.utils.evaluate_template_match
        for details
        """
        user = info.context.user
        file_version = input.get("file_version")
        study = input.get("study")

        # Check if file exists
        _, file_version_id = from_global_id(file_version)
        file_version = None
        try:
            file_version = Version.objects.get(pk=file_version_id)
        except Version.DoesNotExist:
            raise GraphQLError(
                f"File {file_version_id} does not exist"
            )

        # Check if study exists
        _, study_id = from_global_id(study)
        study = None
        try:
            study = Study.objects.get(pk=study_id)
        except Study.DoesNotExist:
            raise GraphQLError(f"Study {study_id} does not exist")

        # Check permissions - user should be able to view file and study
        allowed_view_file = (
            user.has_perm("files.view_file")
            or user.has_perm("files.view_my_file")
        )
        allowed_view_study = (
            user.has_perm("studies.view_study")
            or (
                user.has_perm("studies.view_my_study")
                and user.studies.filter(kf_id=study.pk).exists()
            )
        )
        if not (allowed_view_file and allowed_view_study):
            raise GraphQLError("Not allowed")

        # Validate file content against study templates
        results = []
        for template_version in study.template_versions.all():
            result = evaluate_template_match(file_version, template_version)
            results.append(
                TemplateMatchResult(
                    **result, template_version=template_version
                )
            )

        return EvaluateTemplateMatchMutation(results=results)


class Mutation(graphene.ObjectType):
    create_version = VersionUploadMutation.Field(
        description="Upload a new version of a file"
    )
    update_version = VersionMutation.Field(description="Update a file version")
    evaluate_template_match = EvaluateTemplateMatchMutation.Field(
        description="Evaluate a file version against its study templates"
    )
