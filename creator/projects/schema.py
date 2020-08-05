from graphene import relay, Enum, Field
from graphene_django import DjangoObjectType, DjangoConnectionField
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from graphql_relay import from_global_id
from django_filters import FilterSet, OrderingFilter

from creator.projects.models import Project, PROJECT_TYPES

from creator.projects.mutations import Mutation


ProjectType = Enum(
    "ProjectType",
    [
        (project_type[0], project_type[0].replace("-", "_"))
        for project_type in PROJECT_TYPES
    ],
)


class ProjectNode(DjangoObjectType):
    class Meta:
        model = Project
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, project_id):
        """
        Only return if the user is allowed to view projects
        """
        user = info.context.user

        if not (
            user.has_perm("projects.view_project")
            or user.has_perm("projects.view_my_study_project")
        ):
            raise GraphQLError("Not allowed")

        try:
            project = cls._meta.model.objects.get(project_id=project_id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Project was not found")

        # If user only has view_my_study_project, make sure the project belongs
        # to one of their studies
        if user.has_perm("projects.view_project") or (
            user.has_perm("projects.view_my_study_project")
            and project.study
            and user.studies.filter(kf_id=project.study.kf_id).exists()
        ):
            return project

        raise GraphQLError("Not allowed")


class ProjectFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on", "modified_on"))

    class Meta:
        model = Project
        fields = [
            "name",
            "project_id",
            "project_type",
            "workflow_type",
            "deleted",
            "study",
        ]


class Query(object):
    project = relay.Node.Field(ProjectNode, description="Get a single project")
    all_projects = DjangoFilterConnectionField(
        ProjectNode,
        filterset_class=ProjectFilter,
        description="Get all projects",
    )

    def resolve_all_projects(self, info, **kwargs):
        """
        Return all projects if user has view_project
        Return only projects in user's studies if user has view_my_project
        Return not allowed otherwise
        """
        user = info.context.user

        if not (
            user.has_perm("projects.list_all_project")
            or user.has_perm("projects.view_my_study_project")
        ):
            raise GraphQLError("Not allowed")

        if user.has_perm("projects.list_all_project"):
            return Project.objects.all()

        if user.has_perm("projects.view_my_study_project"):
            return Project.objects.filter(study__in=user.studies.all()).all()

        return Project.objects.none()
