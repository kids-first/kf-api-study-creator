"""
This is the root schema definition that combines individual applications'
schemas into one.
Each application that has queries or mutations exports them as either Query
or Mutation from the application's schema module.
No resolvers or type definitions should be included here.
"""
import graphene
from graphql import GraphQLError
from graphene_django import DjangoObjectType

import creator.analyses.schema
import creator.buckets.schema
import creator.files.schema
import creator.studies.schema
import creator.projects.schema
import creator.users.schema
import creator.referral_tokens.schema
import creator.status.schema
import creator.jobs.schema
import creator.releases.schema
import creator.ingest_runs.schema


class Query(
    creator.analyses.schema.Query,
    creator.files.schema.Query,
    creator.studies.schema.Query,
    creator.users.schema.Query,
    creator.events.schema.Query,
    creator.projects.schema.Query,
    creator.buckets.schema.Query,
    creator.referral_tokens.schema.Query,
    creator.status.schema.Query,
    creator.jobs.schema.Query,
    creator.releases.schema.Query,
    creator.ingest_runs.schema.Query,
    graphene.ObjectType,
):
    """ Root query schema combining all apps' schemas """

    pass


class Mutation(
    creator.analyses.schema.Mutation,
    creator.buckets.schema.Mutation,
    creator.projects.schema.Mutation,
    creator.studies.schema.Mutation,
    creator.files.schema.Mutation,
    creator.users.schema.Mutation,
    creator.referral_tokens.schema.Mutation,
    creator.releases.schema.Mutation,
    creator.ingest_runs.schema.Mutation,
    graphene.ObjectType,
):
    """ Root mutation schema combining all apps' schemas """

    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
