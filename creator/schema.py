import graphene
import creator.files.schema
import creator.studies.schema


class Query(creator.files.schema.Query,
            creator.studies.schema.Query,
            graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    create_file = creator.files.schema.UploadMutation.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
