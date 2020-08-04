import graphene

from creator.files.schema.file import Query as FileQuery
from creator.files.schema.version import Query as VersionQuery
from creator.files.schema.download import Query as DownloadQuery

from creator.files.mutations.file import Mutation as FileMutation
from creator.files.mutations.version import Mutation as VersionMutation
from creator.files.mutations.download import Mutation as DownloadMutation


class Query(FileQuery, VersionQuery, DownloadQuery, graphene.ObjectType):
    pass


class Mutation(
    FileMutation, VersionMutation, DownloadMutation, graphene.ObjectType
):
    pass
