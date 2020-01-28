from django.conf import settings
from graphene import relay, Mutation, Enum, Field, ID, InputObjectType, String
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from graphql_relay import from_global_id
from django_filters import FilterSet, OrderingFilter

from creator.studies.schema import StudyNode
from creator.studies.models import Study
from creator.events.models import Event

from creator.projects.cavatica import sync_cavatica_projects, create_project
from .models import Project, PROJECT_TYPES, WORKFLOW_TYPES


# WorkflowType = Enum(
#     "WorkflowType",
#     [
#         (workflow[0], workflow[0].replace("-", "_"))
#         for workflow in WORKFLOW_TYPES
#     ],
# )

ProjectType = Enum(
    "ProjectType",
    [
        (project_type[0], project_type[0].replace("-", "_"))
        for project_type in PROJECT_TYPES
    ],
)


class ProjectNode(DjangoObjectType):
    # workflow_type = WorkflowType()

    class Meta:
        model = Project
        interfaces = (relay.Node,)
        filter_fields = ()

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
            "study"
        ]


class ProjectInput(InputObjectType):
    workflow_type = String(description="Workflows to be run for this study")
    project_type = Field(
        "creator.projects.schema.ProjectType",
        description="The type of project",
    )
    study = ID(
        required=True,
        description="The study that the new project will belong to",
    )


class CreateProjectMutation(Mutation):
    class Arguments:
        input = ProjectInput(
            required=True, description="Attributes for the new project"
        )

    project = Field(ProjectNode)

    def mutate(self, info, input):
        """
        Create a new project with a given workflow type and study if that study
        does not already have a project with that workflow type.
        """
        if not (
            settings.FEAT_CAVATICA_CREATE_PROJECTS
            and settings.CAVATICA_URL
            and settings.CAVATICA_HARMONIZATION_TOKEN
        ):
            raise GraphQLError(
                "Creating projects is not enabled. "
                "You may need to make sure that the api is configured with a "
                "valid Cavatica url and credentials and that "
                "FEAT_CAVATICA_CREATE_PROJECTS has been set."
            )

        user = info.context.user
        if (
            user is None
            or not user.is_authenticated
            or "ADMIN" not in user.ego_roles
        ):
            raise GraphQLError("Not authenticated to create a project.")

        try:
            _, kf_id = from_global_id(input["study"])
            study = Study.objects.get(kf_id=kf_id)
        except Study.DoesNotExist:
            raise GraphQLError("Study does not exist.")

        if Project.objects.filter(
            workflow_type=input["workflow_type"], study=study
        ).exists():
            raise GraphQLError(
                f"Study already has a {input['workflow_type']} project."
            )
        project = create_project(
            study, input["project_type"], input["workflow_type"]
        )
        return CreateProjectMutation(project=project)


class UpdateProjectInput(InputObjectType):
    """
    Fields that may be updated for a project
    """

    workflow_type = String(description="Workflows to be run for this study")
    project_type = Field(
        "creator.projects.schema.ProjectType",
        description="The type of project",
    )


class UpdateProjectMutation(Mutation):
    class Arguments:
        id = ID(required=True, description="The ID of the project to update")
        input = UpdateProjectInput(
            required=True, description="Attributes for the project"
        )

    project = Field(ProjectNode)

    def mutate(self, info, id, input):
        """
        Update a project
        """
        user = info.context.user
        if (
            user is None
            or not user.is_authenticated
            or "ADMIN" not in user.ego_roles
        ):
            raise GraphQLError("Not authenticated to update a project.")

        try:
            _, project_id = from_global_id(id)
            project = Project.objects.get(project_id=project_id)
        except Project.DoesNotExist:
            raise GraphQLError("Project does not exist.")

        for attr, value in input.items():
            setattr(project, attr, value)
        project.save()

        # Log an event
        message = f"{user.username} updated project {project.project_id}"
        event = Event(
            study=project.study,
            project=project,
            description=message,
            event_type="PR_UPD",
        )
        # Only add the user if they are in the database (not a service user)
        if not user._state.adding:
            event.user = user
        event.save()

        return UpdateProjectMutation(project=project)


class SyncProjectsMutation(Mutation):
    created = DjangoFilterConnectionField(ProjectNode)
    updated = DjangoFilterConnectionField(ProjectNode)
    deleted = DjangoFilterConnectionField(ProjectNode)

    def mutate(self, info):
        created, updated, deleted = sync_cavatica_projects()
        return SyncProjectsMutation(
            created=created, updated=updated, deleted=deleted
        )


class LinkProjectMutation(Mutation):
    """
    Link a project to a study.
    If either do not exist, an error will be returned.
    If both are linked already, nothing will be done.
    May only be performed by an administrator
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

        # Log an event
        message = (
            f"{user.username} linked project {project.project_id} to "
            f"study {study.kf_id}"
        )
        event = Event(
            study=study,
            project=project,
            description=message,
            event_type="PR_LIN",
        )
        # Only add the user if they are in the database (not a service user)
        if user and not user._state.adding:
            event.user = user
        event.save()

        return LinkProjectMutation(project=project, study=study)


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

        # Log an event
        message = (
            f"{user.username} unlinked project {project.project_id} from "
            f"study {study.kf_id}"
        )
        event = Event(
            study=study,
            project=project,
            description=message,
            event_type="PR_UNL",
        )

        # Only add the user if they are in the database (not a service user)
        if user and not user._state.adding:
            event.user = user
        event.save()
        return UnlinkProjectMutation(project=project, study=study)


class Query(object):
    project = relay.Node.Field(ProjectNode, description="Get a single project")
    all_projects = DjangoFilterConnectionField(
        ProjectNode,
        filterset_class=ProjectFilter,
        description="Get all projects",
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
            qs = Project.objects
            if kwargs.get("study") == "":
                qs = qs.filter(study=None)
            return qs.all()

        return Project.objects.none()
