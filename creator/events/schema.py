import graphene
import django_filters
from graphene import relay, ObjectType, Field
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import OrderingFilter

from graphql import GraphQLError

from creator.events.models import Event


class EventNode(DjangoObjectType):
    class Meta:
        model = Event
        interfaces = (relay.Node,)


class EventFilter(django_filters.FilterSet):
    study_kf_id = django_filters.CharFilter(
        field_name="study__kf_id", lookup_expr="exact"
    )
    file_kf_id = django_filters.CharFilter(
        field_name="file__kf_id", lookup_expr="exact"
    )
    version_kf_id = django_filters.CharFilter(
        field_name="version__kf_id", lookup_expr="exact"
    )
    username = django_filters.CharFilter(
        field_name="user__username", lookup_expr="exact"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lt"
    )
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gt"
    )

    class Meta:
        model = Event
        fields = {"event_type": ["exact"]}

    order_by = OrderingFilter(fields=("created_at",))


class Query(object):
    all_events = DjangoFilterConnectionField(
        EventNode, filterset_class=EventFilter, description="List all events"
    )

    def resolve_all_events(self, info, **kwargs):
        """
        Resolves events for given user
        Admins may retrieve all events
        Users may retrieve events related to studies they are in
        Unauthed users may not retrieve events
        """
        user = info.context.user
        if user.has_perm("events.view_event"):
            return Event.objects.all()

        if user.has_perm("events.view_my_event"):
            return Event.objects.filter(study__in=user.studies.all())

        raise GraphQLError("Not allowed")
