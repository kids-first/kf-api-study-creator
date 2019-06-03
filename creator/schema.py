import graphene
import creator.files.schema
import creator.studies.schema
import creator.users.schema


class Query(creator.files.schema.Query,
            creator.studies.schema.Query,
            creator.users.schema.Query,
            graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    create_file = creator.files.schema.file.UploadMutation.Field(
        description=(
            "Upload a new file or version to an existing file and "
            "study"
        )
    )
    update_file = creator.files.schema.file.FileMutation.Field()
    delete_file = creator.files.schema.file.DeleteFileMutation.Field()
    update_version = creator.files.schema.version.VersionMutation.Field()
    signed_url = creator.files.schema.SignedUrlMutation.Field()
    create_dev_token = creator.files.schema.DevDownloadTokenMutation.Field()
    delete_dev_token = (
        creator.files.schema.DeleteDevDownloadTokenMutation.Field()
    )


schema = graphene.Schema(query=Query, mutation=Mutation)
