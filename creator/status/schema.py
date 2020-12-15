import graphene
from django.core.cache import cache
import creator.status.settings.schema


def get_version_info():
    from creator.version_info import COMMIT, VERSION

    return {"commit": COMMIT, "version": VERSION}


class Status(
    graphene.ObjectType,
):
    name = graphene.String()
    version = graphene.String()
    commit = graphene.String()


class Query(graphene.ObjectType):

    status = graphene.Field(Status)

    def resolve_status(parent, info):
        """
        Return status information about the study creator.
        """
        # Retrieve from cache in the case that we have to parse git commands
        # to get version details.
        info = cache.get_or_set("VERSION_INFO", get_version_info)

        return Status(name="Kids First Study Creator", **info)


