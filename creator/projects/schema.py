import re
import django_rq
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
from creator.tasks import import_delivery_files_task

from creator.projects.cavatica import sync_cavatica_projects, create_project
from .models import Project, PROJECT_TYPES


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
            return None

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

        if not user.has_perm("projects.add_project"):
            raise GraphQLError("Not allowed")

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

        regex = re.compile("[~`!@#$%^&*()+}{:;<>?/\\\\|]")
        if not regex.search(input["workflow_type"]) is None:
            raise GraphQLError(
                f"No special characters allowed in workflow type"
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

        if not user.has_perm("projects.change_project"):
            raise GraphQLError("Not allowed")

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
        user = info.context.user

        if not user.has_perm("projects.sync_project"):
            raise GraphQLError("Not allowed")

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

        if not user.has_perm("projects.link_project"):
            raise GraphQLError("Not allowed")

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

        if not user.has_perm("projects.unlink_project"):
            raise GraphQLError("Not allowed")

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


class ImportVolumeFilesMutation(Mutation):
    class Arguments:
        project = ID(
            required=True,
            description="The relay ID of the project to import to",
        )

    project = Field(ProjectNode)

    def mutate(self, info, project):
        user = info.context.user

        if not user.has_perm("projects.import_volume"):
            raise GraphQLError("Not allowed")

        try:
            _, project_id = from_global_id(project)
            project = Project.objects.get(project_id=project_id)
        except (Project.DoesNotExist, UnicodeDecodeError):
            raise GraphQLError("Project does not exist.")

        import_job = django_rq.enqueue(
            import_delivery_files_task, project.project_id, user.sub
        )
        return ImportVolumeFilesMutation(project=project)


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
