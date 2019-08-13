from graphene import relay, Mutation
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from creator.projects.cavatica import sync_cavatica_projects
from .models import Project


class ProjectNode(DjangoObjectType):
    class Meta:
        model = Project
        filter_fields = ["name", "project_id", "project_type", "workflow_type"]
        interfaces = (relay.Node,)

    @classmethod
    def get_node(cls, info, project_id):
        """
        Only return node if user is Cavatica data scientist
        """

        user = info.context.user

        if not user.is_authenticated:
            return Project.objects.none()

        try:
            project = Project.objects.get(project_id=project_id)
        except Project.DoesNotExist:
            return Project.objects.none()

        if user.is_admin:
            return project

        return Project.objects.none()


class SyncProjectsMutation(Mutation):
    created = DjangoFilterConnectionField(ProjectNode)
    updated = DjangoFilterConnectionField(ProjectNode)

    def mutate(self, info):
        created, updated = sync_cavatica_projects()
        return SyncProjectsMutation(created=created, updated=updated)


class Query(object):
    project = relay.Node.Field(ProjectNode)
    all_projects = DjangoFilterConnectionField(ProjectNode)

    def resolve_all_projects(self, info, **kwargs):
        """
        If user is ADMIN, return all Cavatica projects
        If user is unauthed, return no Cavatica projects
        """
        user = info.context.user

        if not user.is_authenticated or user is None:
            return Project.objects.none()

        if user.is_admin:
            return Project.objects.all()

        return Project.objects.none()
