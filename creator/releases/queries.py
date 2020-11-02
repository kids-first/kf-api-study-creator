from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField, GlobalIDFilter
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter

from creator.releases.nodes import (
    ReleaseNode,
    ReleaseTaskNode,
    ReleaseServiceNode,
    ReleaseEventNode,
)
from creator.releases.models import (
    Release,
    ReleaseTask,
    ReleaseService,
    ReleaseEvent,
)


class ReleaseFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_at",))

    class Meta:
        model = Release
        fields = {"state": ["exact"]}


class ReleaseTaskFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_at",))

    release = GlobalIDFilter()

    class Meta:
        model = Release
        fields = {"state": ["exact"]}


class ReleaseServiceFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_at",))

    class Meta:
        model = ReleaseService
        fields = {"enabled": ["exact"]}


class ReleaseEventFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_at",))

    release = GlobalIDFilter()
    release_service = GlobalIDFilter()
    task = GlobalIDFilter()

    class Meta:
        model = ReleaseEvent
        fields = {"event_type": ["exact"]}


class Query(object):
    release = relay.Node.Field(ReleaseNode, description="Get a single release")
    all_releases = DjangoFilterConnectionField(
        ReleaseNode,
        filterset_class=ReleaseFilter,
        description="Get all releases",
    )

    def resolve_all_releases(self, info, **kwargs):
        """
        Return all releases
        """
        user = info.context.user

        if not user.has_perm("releases.list_all_release"):
            raise GraphQLError("Not allowed")

        return Release.objects.all()

    release_task = relay.Node.Field(
        ReleaseTaskNode, description="Get a single release task"
    )
    all_release_tasks = DjangoFilterConnectionField(
        ReleaseTaskNode,
        filterset_class=ReleaseTaskFilter,
        description="Get all release tasks",
    )

    def resolve_all_release_tasks(self, info, **kwargs):
        """
        Return all release tasks
        """
        user = info.context.user

        if not user.has_perm("releases.list_all_releasetask"):
            raise GraphQLError("Not allowed")

        return ReleaseTask.objects.all()

    release_service = relay.Node.Field(
        ReleaseServiceNode, description="Get a single release service"
    )
    all_release_services = DjangoFilterConnectionField(
        ReleaseServiceNode,
        filterset_class=ReleaseServiceFilter,
        description="Get all release services",
    )

    def resolve_all_release_services(self, info, **kwargs):
        """
        Return all release services
        """
        user = info.context.user

        if not user.has_perm("releases.list_all_releaseservice"):
            raise GraphQLError("Not allowed")

        return ReleaseService.objects.all()

    release_event = relay.Node.Field(
        ReleaseEventNode, description="Get a single release event"
    )
    all_release_events = DjangoFilterConnectionField(
        ReleaseEventNode,
        filterset_class=ReleaseEventFilter,
        description="Get all release events",
    )

    def resolve_all_release_events(self, info, **kwargs):
        """
        Return all release events
        """
        user = info.context.user

        if not user.has_perm("releases.list_all_releaseevent"):
            raise GraphQLError("Not allowed")

        return ReleaseEvent.objects.all()
