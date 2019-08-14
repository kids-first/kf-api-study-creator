from graphene import relay, Mutation, Field, ID
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from graphql_relay import from_global_id

from creator.studies.schema import StudyNode
from creator.studies.models import Study

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


class LinkProjectMutation(Mutation):
    project = Field(ProjectNode)
    study = Field(StudyNode)

    class Arguments:
        project = ID(required=True)
        study = ID(required=True)

    def mutate(self, info, project, study):
        user = info.context.user

        if not user.is_authenticated or user is None or not user.is_admin:
            raise GraphQLError("Not authenticated to link a project.")

        try:
            _, project_id = from_global_id(project)
            project = Project.objects.get(project_id=project_id)
        except (Project.DoesNotExist, UnicodeDecodeError):
            raise GraphQLError("Project does not exist.")

        try:
            _, study_id = from_global_id(study)
            study = Study.objects.get(kf_id=study_id)
        except (Study.DoesNotExist, UnicodeDecodeError):
            raise GraphQLError("Study does not exist.")

        project.study = study
        project.save()
        return project


class UnlinkProjectMutation(Mutation):
    """
    Unlink a project from a study.
    If either do not exist, an error will be returned.
    If they are not linked already, nothing will be done.
    May only be performed by an administrator.
    """

    project = Field(ProjectNode)
    study = Field(StudyNode)

    class Arguments:
        project = ID(
            required=True, description="The relay ID of the project to link"
        )
        study = ID(
            required=True,
            description="The relay ID of the study to link the project to",
        )

    def mutate(self, info, project, study):
        user = info.context.user

        if not user.is_authenticated or user is None or not user.is_admin:
            raise GraphQLError("Not authenticated to unlink a project.")

        try:
            _, project_id = from_global_id(project)
            project = Project.objects.get(project_id=project_id)
        except (Project.DoesNotExist, UnicodeDecodeError):
            raise GraphQLError("Project does not exist.")

        try:
            _, study_id = from_global_id(study)
            study = Study.objects.get(kf_id=study_id)
        except (Study.DoesNotExist, UnicodeDecodeError):
            raise GraphQLError("Study does not exist.")

        project.study = None
        project.save()
        return UnlinkProjectMutation(project=project, study=study)


class Query(object):
    project = relay.Node.Field(ProjectNode, description="Get a single project")
    all_projects = DjangoFilterConnectionField(
        ProjectNode, description="Get all projects"
    )

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
