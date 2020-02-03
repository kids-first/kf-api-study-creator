import graphene
from django.conf import settings
from django.core.cache import cache
import creator.files.schema
import creator.studies.schema
import creator.users.schema
import creator.events.schema
import creator.projects.schema


def get_version_info():
    from creator.version_info import COMMIT, VERSION

    return {"commit": COMMIT, "version": VERSION}


class Features(graphene.ObjectType):
    study_creation = graphene.Boolean(
        description=(
            "Will create new studies in the dataservice when a createStudy "
            "mutation is performed"
        )
    )
    study_updates = graphene.Boolean(
        description=(
            "Studies will be updated in the dataservice when "
            "changed through an updateStudy mutation"
        )
    )
    cavatica_create_projects = graphene.Boolean(
        description=(
            "Cavatica projects may be created through the createProject "
            "mutation"
        )
    )
    cavatica_copy_users = graphene.Boolean(
        description=(
            "Users will be copied from the CAVATICA_USER_ACCESS_PROJECT to "
            "any new project"
        )
    )
    cavatica_mount_volumes = graphene.Boolean(
        description=(
            "New projects will automatically have a new S3 volume mounted"
        )
    )
    bucketservice_create_buckets = graphene.Boolean(
        description=(
            "New buckets will be created for new studies via the bucketservice"
            " when a new study is created"
        )
    )


class Status(graphene.ObjectType):
    name = graphene.String()
    version = graphene.String()
    commit = graphene.String()
    features = graphene.Field(Features)


class Query(
    creator.files.schema.Query,
    creator.studies.schema.Query,
    creator.users.schema.Query,
    creator.events.schema.Query,
    creator.projects.schema.Query,
    graphene.ObjectType,
):
    status = graphene.Field(Status)

    def resolve_status(parent, info):
        """
        Return status information about the study creator.
        """
        # Retrieve from cache in the case that we have to parse git commands
        # to get version details.
        info = cache.get_or_set("VERSION_INFO", get_version_info)

        features = {
            "study_creation": settings.FEAT_DATASERVICE_CREATE_STUDIES,
            "study_updates": settings.FEAT_DATASERVICE_UPDATE_STUDIES,
            "cavatica_create_projects": settings.FEAT_CAVATICA_CREATE_PROJECTS,
            "cavatica_copy_users": settings.FEAT_CAVATICA_COPY_USERS,
            "cavatica_mount_volumes": settings.FEAT_CAVATICA_MOUNT_VOLUMES,
            "bucketservice_create_buckets": (
                settings.FEAT_BUCKETSERVICE_CREATE_BUCKETS
            ),
        }
        features = Features(**features)

        return Status(
            name="Kids First Study Creator", **info, features=features
        )


class Mutation(graphene.ObjectType):
    create_file = creator.files.schema.file.FileUploadMutation.Field(
        description="Upload a new file to a study"
    )
    create_version = creator.files.schema.version.VersionUploadMutation.Field(
        description="Upload a new version of a file"
    )
    update_file = creator.files.schema.file.FileMutation.Field(
        description="Update a file"
    )
    delete_file = creator.files.schema.file.DeleteFileMutation.Field(
        description="Delete a file"
    )
    update_version = creator.files.schema.version.VersionMutation.Field(
        description="Update a file version"
    )
    signed_url = creator.files.schema.SignedUrlMutation.Field(
        description="Create a new signed url"
    )
    create_dev_token = creator.files.schema.DevDownloadTokenMutation.Field(
        description="Create a new developer token"
    )
    delete_dev_token = (
        creator.files.schema.DeleteDevDownloadTokenMutation.Field(
            description="Delete a developer token"
        )
    )

    subscribe_to = creator.users.schema.SubscribeToMutation.Field(
        description="Subscribe the current user to a study"
    )
    unsubscribe_from = creator.users.schema.UnsubscribeFromMutation.Field(
        description="Unsubscribe the current user from a study"
    )
    update_my_profile = creator.users.schema.MyProfileMutation.Field(
        description="Update the currently logged in user's profile"
    )
    create_study = creator.studies.schema.CreateStudyMutation.Field(
        description="""Create a new study including setup in external systems.
        This involves: creating the study in the dataservice, mirroring the
        study in the study-creator api, creating a new bucket for the study
        data, and setting up new projects in Cavatica."""
    )
    update_study = creator.studies.schema.UpdateStudyMutation.Field(
        description="Update a given study"
    )
    create_project = creator.projects.schema.CreateProjectMutation.Field(
        description="Create a new project for a study"
    )
    update_project = creator.projects.schema.UpdateProjectMutation.Field(
        description="Update an existing project"
    )
    sync_projects = creator.projects.schema.SyncProjectsMutation.Field(
        description=(
            "Synchronize projects in the study creator api with "
            "project in Cavatica"
        )
    )
    link_project = creator.projects.schema.LinkProjectMutation.Field(
        description="Link a Cavatica project to a Study"
    )
    unlink_project = creator.projects.schema.UnlinkProjectMutation.Field(
        description="Unlink a Cavatica project from a Study"
    )


schema = graphene.Schema(query=Query, mutation=Mutation)
