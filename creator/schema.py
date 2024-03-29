"""
This is the root schema definition that combines individual applications'
schemas into one.
Each application that has queries or mutations exports them as either Query
or Mutation from the application's schema module.
No resolvers or type definitions should be included here.
"""
import graphene
from django.conf import settings

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
import creator.data_reviews.schema
import creator.ingest_runs.schema
import creator.organizations.schema
import creator.data_templates.schema


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
    creator.data_reviews.schema.Query,
    creator.ingest_runs.schema.Query,
    creator.organizations.schema.Query,
    creator.data_templates.schema.Query,
    graphene.ObjectType,
):
    """ Root query schema combining all apps' schemas """

    node = graphene.relay.Node.Field()
    if settings.DEBUG:
        from graphene_django.debug import DjangoDebug

        debug = graphene.Field(DjangoDebug, name="_debug")


class Mutation(
    creator.analyses.schema.Mutation,
    creator.buckets.schema.Mutation,
    creator.projects.schema.Mutation,
    creator.studies.schema.Mutation,
    creator.files.schema.Mutation,
    creator.users.schema.Mutation,
    creator.referral_tokens.schema.Mutation,
    creator.status.schema.Mutation,
    creator.releases.schema.Mutation,
    creator.data_reviews.schema.Mutation,
    creator.ingest_runs.schema.Mutation,
    creator.organizations.schema.Mutation,
    creator.data_templates.schema.Mutation,
    graphene.ObjectType,
):
    """ Root mutation schema combining all apps' schemas """

    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
