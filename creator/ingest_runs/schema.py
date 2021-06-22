import graphene

from creator.ingest_runs.queries.ingest_run import Query as IngestRunQuery
from creator.ingest_runs.queries.validation_run import (
    Query as ValidationRunQuery,
)
from creator.ingest_runs.mutations.ingest_run import (
    Mutation as IngestRunMutation,
)
from creator.ingest_runs.mutations.validation_run import (
    Mutation as ValidationRunMutation,
)


class Query(IngestRunQuery, ValidationRunQuery, graphene.ObjectType):
    pass


class Mutation(IngestRunMutation, ValidationRunMutation, graphene.ObjectType):
    pass
