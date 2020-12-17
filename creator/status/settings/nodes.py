import graphene


class Features(graphene.ObjectType):
    study_creation = graphene.Boolean(
        description=(
            "Will create new studies in the dataservice when a createStudy "
            "mutation is performed"
        )
    )
    study_updates = graphene.Boolean(
        description=(
            "Studies will be updated in the dataservice when "
            "changed through an updateStudy mutation"
        )
    )
    cavatica_create_projects = graphene.Boolean(
        description=(
            "Cavatica projects may be created through the createProject "
            "mutation"
        )
    )
    cavatica_copy_users = graphene.Boolean(
        description=(
            "Users will be copied from the CAVATICA_USER_ACCESS_PROJECT to "
            "any new project"
        )
    )
    cavatica_mount_volumes = graphene.Boolean(
        description=(
            "New projects will automatically have a new S3 volume mounted"
        )
    )
    study_buckets_create_buckets = graphene.Boolean(
        description=(
            "New buckets will be created for new studies when a new study is "
            "created"
        )
    )
    create_slack_channels = graphene.Boolean(
        description=("Create a Slack channel for new studies")
    )
    slack_send_release_notifications = graphene.Boolean(
        description="Send notifications to slack for changes in release states"
    )


class Settings(graphene.ObjectType):
    development_endpoints = graphene.Boolean(
        description=("Developer endpoints are active")
    )
    dataservice_url = graphene.String(description="The URL of the Dataservice")
    cavatica_url = graphene.String(description="The URL of the Cavatica API")
    cavatica_delivery_account = graphene.String(
        description="The Cavatica account used for delivery projects"
    )
    cavatica_harmonization_account = graphene.String(
        description=(
            "The Cavatica account used for harmonization and " "other projects"
        )
    )
    cavatica_user_access_project = graphene.String(
        description="The project to copy users from for new projects"
    )
    study_buckets_region = graphene.String(
        description=("The AWS region where new study buckets will be created")
    )
    study_buckets_logging_bucket = graphene.String(
        description=(
            "The bucket where access logs for the new study buckets will be "
            "stored"
        )
    )
    study_buckets_dr_region = graphene.String(
        description=(
            "The AWS region where new study buckets recovery buckets "
            "will be created"
        )
    )
    study_buckets_dr_logging_bucket = graphene.String(
        description=(
            "The bucket where access logs for the new study bucket recovery "
            "buckets will be stored"
        )
    )
    study_buckets_inventory_location = graphene.String(
        description=(
            "The full aws bucket with prefix where bucket inventories will be "
            "dumped"
        )
    )
    study_buckets_log_prefix = graphene.String(
        description=(
            "The prefix under which access logs will be stored in the logging "
            "and dr logging buckets"
        )
    )
    slack_users = graphene.List(
        graphene.String,
        description=("Slack IDs of users to add to new study channels"),
    )
    log_bucket = graphene.String(description="S3 bucket to store job logs in")
    log_dir = graphene.String(
        description="Prefix to store files under in the log bucket"
    )
