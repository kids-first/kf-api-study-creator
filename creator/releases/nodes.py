from graphene import relay
from graphql_relay import from_global_id
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.releases.models import (
    Release,
    ReleaseTask,
    ReleaseService,
    ReleaseEvent,
)


class ReleaseNode(DjangoObjectType):
    class Meta:
        model = Release
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        if not (user.has_perm("releases.view_release")):
            raise GraphQLError("Not allowed")

        try:
            release = cls._meta.model.objects.get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Releases was not found")

        return release


class ReleaseTaskNode(DjangoObjectType):
    class Meta:
        model = ReleaseTask
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        if not (user.has_perm("releases.view_releasetask")):
            raise GraphQLError("Not allowed")

        try:
            release_task = cls._meta.model.objects.get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Release Task was not found")

        return release_task


class ReleaseServiceNode(DjangoObjectType):
    class Meta:
        model = ReleaseService
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        if not (user.has_perm("releases.view_releaseservice")):
            raise GraphQLError("Not allowed")

        try:
            release_service = cls._meta.model.objects.get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Release Service was not found")

        return release_service


class ReleaseEventNode(DjangoObjectType):
    class Meta:
        model = ReleaseEvent
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        if not (user.has_perm("releases.view_releaseevent")):
            raise GraphQLError("Not allowed")

        try:
            event = cls._meta.model.objects.get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Release Event was not found")

        return event
