import graphene
import creator.files.schema
import creator.studies.schema
import creator.users.schema
import creator.events.schema
import creator.projects.schema


class Query(
    creator.files.schema.Query,
    creator.studies.schema.Query,
    creator.users.schema.Query,
    creator.events.schema.Query,
    creator.projects.schema.Query,
    graphene.ObjectType,
):
    pass


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
