import graphene
import django_filters
from django.conf import settings
from graphene import relay, Field, String
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_s3_storage.storage import S3Storage
from graphene_file_upload.scalars import Upload
from django_filters import OrderingFilter
from graphql import GraphQLError

from botocore.exceptions import ClientError

from ..models import File, Version


class VersionNode(DjangoObjectType):
    class Meta:
        model = Version
        interfaces = (relay.Node,)

    download_url = graphene.String()

    def resolve_download_url(self, info):
        return f"{info.context.scheme}://{info.context.get_host()}{self.path}"

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


class VersionFilter(django_filters.FilterSet):
    file_kf_id = django_filters.CharFilter(
        field_name="root_file__kf_id", lookup_expr="exact"
    )

    class Meta:
        model = Version
        fields = []

    order_by = OrderingFilter(fields=("created_at",))


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
        if user is None or not user.is_authenticated:
            raise GraphQLError("Not authenticated to mutate a version.")

        try:
            version = Version.objects.get(kf_id=kf_id)
        except Version.DoesNotExist:
            raise GraphQLError("Version does not exist.")

        study_id = version.root_file.study.kf_id
        if study_id not in user.ego_groups and "ADMIN" not in user.ego_roles:
            raise GraphQLError("Not authenticated to mutate a version.")

        try:
            if kwargs.get("description"):
                version.description = kwargs.get("description")
            if kwargs.get("state"):
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
            required=True,
            description="kf_id of the file this version will belong to",
        )
        description = graphene.String(
            required=True,
            description=(
                "A description of the changes made in this version to"
                " the file"
            ),
        )

    success = graphene.Boolean()
    version = graphene.Field(VersionNode)

    def mutate(self, info, file, fileId, description, **kwargs):
        """
        Uploads a new version of a file given a fileId.
        """
        user = info.context.user
        if user is None or not user.is_authenticated:
            raise GraphQLError("Not authenticated to upload a file.")

        # Try to look up the file specified
        try:
            root_file = File.objects.get(kf_id=fileId)
        except File.DoesNotExist:
            raise GraphQLError("File does not exist.")

        study = root_file.study

        # The user should be allowed to access the relevant file's study
        if (
            study.kf_id not in user.ego_groups
            and "ADMIN" not in user.ego_roles
        ):
            raise GraphQLError("Not authenticated to upload to the study.")

        if file.size > settings.FILE_MAX_SIZE:
            raise GraphQLError("File is too large.")

        try:
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

        return VersionUploadMutation(success=True, version=version)


class VersionQuery(object):
    version = relay.Node.Field(VersionNode, description="Get a version")
    version_by_kf_id = Field(
        VersionNode,
        kf_id=String(required=True),
        description="Get a version by its kf_id",
    )
    all_versions = DjangoFilterConnectionField(
        VersionNode,
        filterset_class=VersionFilter,
        description="List all versions",
    )

    def resolve_version_by_kf_id(self, info, kf_id):
        return VersionNode.get_node(info, kf_id)

    def resolve_all_versions(self, info, **kwargs):
        """
        If user is USER, only return the file versions from the studies
        which the user belongs to
        If user is ADMIN, return all file versions
        If user is unauthed, return no file versions
        """
        user = info.context.user

        if not user.is_authenticated or user is None:
            return Version.objects.none()

        if user.is_admin:
            return Version.objects.all()

        return Version.objects.filter(
            root_file__study__kf_id__in=user.ego_groups
        )