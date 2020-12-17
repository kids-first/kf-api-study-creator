import creator.status.settings.queries
import creator.status.banners.queries
import creator.status.banners.mutations


class Query(
    creator.status.settings.queries.Query,
    creator.status.banners.queries.Query,
):
    pass


class Mutation(
    creator.status.banners.mutations.Mutation,
):
    pass
