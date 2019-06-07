import graphene
import creator.files.schema
import creator.studies.schema
import creator.users.schema
import creator.events.schema


class Query(
    creator.files.schema.Query,
    creator.studies.schema.Query,
    creator.users.schema.Query,
    creator.events.schema.Query,
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
    update_file = creator.files.schema.file.FileMutation.Field()
    delete_file = creator.files.schema.file.DeleteFileMutation.Field()
    update_version = creator.files.schema.version.VersionMutation.Field()
    signed_url = creator.files.schema.SignedUrlMutation.Field()
    create_dev_token = creator.files.schema.DevDownloadTokenMutation.Field()
    delete_dev_token = (
        creator.files.schema.DeleteDevDownloadTokenMutation.Field()
    )
    subscribe_to = creator.users.schema.SubscribeToMutation.Field()
    unsubscribe_from = creator.users.schema.UnsubscribeFromMutation.Field()
    update_my_profile = creator.users.schema.MyProfileMutation.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
