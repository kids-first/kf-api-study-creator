import graphene
import creator.files.schema
import creator.studies.schema


class Query(creator.files.schema.Query,
            creator.studies.schema.Query,
            graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)
