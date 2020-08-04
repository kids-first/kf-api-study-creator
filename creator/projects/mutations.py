import django_rq
import graphene
import re
from django.conf import settings
from graphene_django import DjangoConnectionField
from graphql import GraphQLError
from graphql_relay import from_global_id

from creator.tasks import import_delivery_files_task
from creator.projects.cavatica import sync_cavatica_projects, create_project
from creator.projects.models import Project
from creator.studies.models import Study
from creator.events.models import Event


class ProjectInput(graphene.InputObjectType):
    workflow_type = graphene.String(
        description="Workflows to be run for this study"
    )
    project_type = graphene.Field(
        "creator.projects.schema.ProjectType",
        description="The type of project",
    )
    study = graphene.ID(
        required=True,
        description="The study that the new project will belong to",
    )


class CreateProjectMutation(graphene.Mutation):
    class Arguments:
        input = ProjectInput(
            required=True, description="Attributes for the new project"
        )

    project = graphene.Field("creator.projects.schema.ProjectNode")

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


class UpdateProjectInput(graphene.InputObjectType):
    """
    Fields that may be updated for a project
    """

    workflow_type = graphene.String(
        description="Workflows to be run for this study"
    )
    project_type = graphene.Field(
        "creator.projects.schema.ProjectType",
        description="The type of project",
    )


class UpdateProjectMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the project to update"
        )
        input = UpdateProjectInput(
            required=True, description="Attributes for the project"
        )

    project = graphene.Field("creator.projects.schema.ProjectNode")

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


class SyncProjectsMutation(graphene.Mutation):
    created = DjangoConnectionField("creator.projects.schema.ProjectNode")
    updated = DjangoConnectionField("creator.projects.schema.ProjectNode")
    deleted = DjangoConnectionField("creator.projects.schema.ProjectNode")

    def mutate(self, info):
        user = info.context.user

        if not user.has_perm("projects.sync_project"):
            raise GraphQLError("Not allowed")

        created, updated, deleted = sync_cavatica_projects()
        return SyncProjectsMutation(
            created=created, updated=updated, deleted=deleted
        )


class LinkProjectMutation(graphene.Mutation):
    """
    Link a project to a study.
    If either do not exist, an error will be returned.
    If both are linked already, nothing will be done.
    May only be performed by an administrator
    """

    project = graphene.Field("creator.projects.schema.ProjectNode")
    study = graphene.Field("creator.studies.schema.StudyNode")

    class Arguments:
        project = graphene.ID(
            required=True, description="The relay ID of the project to link"
        )
        study = graphene.ID(
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


class UnlinkProjectMutation(graphene.Mutation):
    """
    Unlink a project from a study.
    If either do not exist, an error will be returned.
    If they are not linked already, nothing will be done.
    May only be performed by an administrator.
    """

    project = graphene.Field("creator.projects.schema.ProjectNode")
    study = graphene.Field("creator.studies.schema.StudyNode")

    class Arguments:
        project = graphene.ID(
            required=True, description="The relay ID of the project to link"
        )
        study = graphene.ID(
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


class ImportVolumeFilesMutation(graphene.Mutation):
    class Arguments:
        project = graphene.ID(
            required=True,
            description="The relay ID of the project to import to",
        )

    project = graphene.Field("creator.projects.schema.ProjectNode")

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


class Mutation(graphene.ObjectType):
    create_project = CreateProjectMutation.Field(
        description="Create a new project for a study"
    )
    update_project = UpdateProjectMutation.Field(
        description="Update an existing project"
    )
    sync_projects = SyncProjectsMutation.Field(
        description=(
            "Synchronize projects in the study creator api with "
            "project in Cavatica"
        )
    )
    link_project = LinkProjectMutation.Field(
        description="Link a Cavatica project to a Study"
    )
    unlink_project = UnlinkProjectMutation.Field(
        description="Unlink a Cavatica project from a Study"
    )
    import_volume_files = ImportVolumeFilesMutation.Field(
        description="Unlink a Cavatica project from a Study"
    )
