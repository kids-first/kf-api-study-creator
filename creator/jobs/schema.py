import django_filters
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, OrderingFilter
from graphql import GraphQLError

from creator.jobs.models import Job, JobLog


class JobFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on", "last_run", "name"))

    class Meta:
        model = Job
        fields = ["name", "active", "failing"]


class JobNode(DjangoObjectType):
    enqueued_at = graphene.DateTime()

    class Meta:
        model = Job
        interfaces = (graphene.relay.Node,)

    @classmethod
    def get_node(cls, info, name):
        """
        Only return node if user is admin
        """
        user = info.context.user

        if not user.has_perm("jobs.view_job"):
            return Job.objects.none()

        return Job.objects.get(name=name)


class JobLogFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_at",))
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lt"
    )
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gt"
    )

    class Meta:
        model = JobLog
        fields = ["job"]


class JobLogNode(DjangoObjectType):
    class Meta:
        model = JobLog
        interfaces = (relay.Node,)
        filter_fields = ()
        exclude = ("log_file",)

    download_url = graphene.String()

    def resolve_download_url(self, info):
        return f"https://{info.context.get_host()}{self.path}"

    @classmethod
    def get_node(cls, info, id):
        """
        """
        user = info.context.user
        if not user.has_perm("jobs.view_joblog"):
            raise GraphQLError("Not allowed")

        try:
            return cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Job Log not found")

        return None


class Query(object):
    job = relay.Node.Field(JobNode, description="Get a single job")
    all_jobs = DjangoFilterConnectionField(
        JobNode, filterset_class=JobFilter, description="Get job statuses"
    )

    def resolve_all_jobs(self, info, **kwargs):
        """
        Return all Jobs
        """
        user = info.context.user
        if not user.has_perm("jobs.list_all_job"):
            raise GraphQLError("Not allowed")

        return Job.objects.all()

    job_log = relay.Node.Field(JobLogNode, description="Get a single job log")
    all_job_logs = DjangoFilterConnectionField(
        JobLogNode,
        filterset_class=JobLogFilter,
        description="Get all job logs",
    )

    def resolve_all_job_logs(self, info, **kwargs):
        """
        Return all Job Logs
        """
        user = info.context.user
        if not user.has_perm("jobs.list_all_joblog"):
            raise GraphQLError("Not allowed")

        return JobLog.objects.all()
