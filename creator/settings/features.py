# FEATURES #####################################################################
# This file contains features that may be toggled on and off and may require
# additional configuration to work properly.

import os


# STUDIES ######################################################################
# The Study Creator's primary purpose is to create and track studies.

# New studies created in the Study Creator should also be created in the
# Dataservice
FEAT_DATASERVICE_CREATE_STUDIES = os.environ.get(
    "FEAT_DATASERVICE_CREATE_STUDIES", True
)

# Any updates to studies in the Study Creator will be sent to the Dataservice
FEAT_DATASERVICE_UPDATE_STUDIES = os.environ.get(
    "FEAT_DATASERVICE_UPDATE_STUDIES", True
)


# S3 Buckets ###################################################################
# The Study Creator needs to create and monitor S3 resources responsible for
# storing the DRC's genomic and clinical data.

# The aws region where the study buckets will be created
STUDY_BUCKETS_REGION = os.environ.get("STUDY_BUCKETS_REGION", "us-east-1")

# The name of the bucket where bucket access logs will be stored for study
# buckets
STUDY_BUCKETS_LOGGING_BUCKET = os.environ.get("STUDY_BUCKETS_LOGGING_BUCKET")

# The prefix where bucket logs will be stored
STUDY_BUCKETS_LOG_PREFIX = os.environ.get(
    "STUDY_BUCKETS_LOG_PREFIX", "/studies/dev/"
)

# Whether or not to create replication buckets
FEAT_STUDY_BUCKETS_REPLICATION_ENABLED = (
    os.environ.get("FEAT_STUDY_BUCKETS_REPLICATION_ENABLED", "True").lower()
    == "true"
)

# The aws region where data recovery buckets will be stored
STUDY_BUCKETS_DR_REGION = os.environ.get(
    "STUDY_BUCKETS_DR_REGION", "us-west-2")

# The name of the bucket where bucket access logs will be stored for data
# recovery buckets
STUDY_BUCKETS_DR_LOGGING_BUCKET = os.environ.get(
    "STUDY_BUCKETS_DR_LOGGING_BUCKET"
)

# Location where the study bucket inventories will be dumped
STUDY_BUCKETS_INVENTORY_LOCATION = os.environ.get(
    "STUDY_BUCKETS_INVENTORY_LOCATION", ""
)
# The IAM role to use when configuring bucket replication
STUDY_BUCKETS_REPLICATION_ROLE = os.environ.get(
    "STUDY_BUCKETS_REPLICATION_ROLE"
)


# CAVATICA #####################################################################
# The Study Creator can create new projects within Cavatica.
# There are two minimal projects for each study: delivery and harmonization.
# Each is setup in its own account.
# Other projects, such as research or analysis projects are created in the
# harmonization account.

# The URL of the Cavatica API
CAVATICA_URL = os.environ.get(
    "CAVATICA_URL", "https://cavatica-api.sbgenomics.com/v2"
)

# Allow creation of new projects in Cavatica for manually for existing studies
# and automatically for new studies
FEAT_CAVATICA_CREATE_PROJECTS = os.environ.get(
    "FEAT_CAVATICA_CREATE_PROJECTS", True
)

# Copy users from the CAVATICA_USER_ACCESS_PROJECT to new projects on creation
FEAT_CAVATICA_COPY_USERS = os.environ.get("FEAT_CAVATICA_COPY_USERS", True)

# Attach study buckets to new Cavatica projects on creation
FEAT_CAVATICA_MOUNT_VOLUMES = os.environ.get(
    "FEAT_CAVATICA_MOUNT_VOLUMES", False
)

# The name of the account to create harmonization projects in
CAVATICA_HARMONIZATION_ACCOUNT = os.environ.get(
    "CAVATICA_HARMONIZATION_ACCOUNT", None
)
# The developer token for the harmonization acconut
CAVATICA_HARMONIZATION_TOKEN = os.environ.get(
    "CAVATICA_HARMONIZATION_TOKEN", None
)
# The name of the account to create delivery projects in
CAVATICA_DELIVERY_ACCOUNT = os.environ.get("CAVATICA_DELIVERY_ACCOUNT", None)
# The developer token for the delivery acconut
CAVATICA_DELIVERY_TOKEN = os.environ.get("CAVATICA_DELIVERY_TOKEN", None)

# The default workflows to setup for new studies
# Each workflow will be given its own project in Cavatcia
CAVATICA_DEFAULT_WORKFLOWS = os.environ.get(
    "CAVATICA_DEFAULT_WORKFLOWS", ""
).split()

# The project_id of the Cavatica project which will be used to clone user
# access grants
CAVATICA_USER_ACCESS_PROJECT = os.environ.get(
    "CAVATICA_USER_ACCESS_PROJECT", "kids-first-drc/user-access"
)

# AWS keys used to attach volumes in Cavatica
CAVATICA_READ_ACCESS_KEY = os.environ.get("CAVATICA_READ_ACCESS_KEY")
CAVATICA_READ_SECRET_KEY = os.environ.get("CAVATICA_READ_SECRET_KEY")
CAVATICA_READWRITE_ACCESS_KEY = os.environ.get("CAVATICA_READWRITE_ACCESS_KEY")
CAVATICA_READWRITE_SECRET_KEY = os.environ.get("CAVATICA_READWRITE_SECRET_KEY")


# Create buckets for new studies
FEAT_STUDY_BUCKETS_CREATE_BUCKETS = os.environ.get(
    "FEAT_STUDY_BUCKETS_CREATE_BUCKETS", False
)


# SLACK ########################################################################
# The Study Creator can communicate with Slack to share information such as
# daily activity or data release statuses.
# To use Slack features, create an app with a bot user and give the Bot User's
# OAuth access token as SLACK_TOKEN.

# Slack OAuth access token for the bot user. Should begin with 'xoxb-'
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")


# Whether to create Slack channels for new studies
FEAT_SLACK_CREATE_CHANNELS = os.environ.get(
    "FEAT_SLACK_CREATE_CHANNELS", False)

# Slack user IDs for users to add to new channels created for studies
# User IDs should be separated by commas
SLACK_USERS = os.environ.get("SLACK_USERS", "").split(",")


# Whether Slack notifications about releases should be sent
FEAT_SLACK_SEND_RELEASE_NOTIFICATIONS = (
    os.environ.get("FEAT_SLACK_SEND_RELEASE_NOTIFICATIONS", "True") == "True"
)

# Channel to post release notifications to
SLACK_RELEASE_CHANNEL = os.environ.get(
    "SLACK_RELEASE_CHANNEL", "#release-notifications"
)

# Slack message chunks limit
SLACK_BLOCK_LIMIT = 50


# GWO INGEST RUNS ##############################################################
# The Study Creator can automate various ingest processes such as ingesting
# harmonized genomic files.

FEAT_INGEST_GENOMIC_WORKFLOW_OUTPUTS = os.environ.get(
    "FEAT_INGEST_GENOMIC_WORKFLOW_OUTPUTS", "True"
)


# EMAIL ########################################################################
# The Study Creator can utilize email to send invites to new users
# Make sure that Django's EMAIL_ settings are configured correctly to utilize
# this feature.

# Set default from email
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "data-tracker@kidsfirstdrc.org"
)

# How many days to expire a referral token
REFERRAL_TOKEN_EXPIRATION_DAYS = os.environ.get(
    "REFERRAL_TOKEN_EXPIRATION_DAYS", 3
)

# Default data tracker url
DATA_TRACKER_URL = os.environ.get(
    "DATA_TRACKER_URL", "https://kf-ui-data-tracker.kidsfirstdrc.org"
)
# The url of the Dataservice API
DATASERVICE_URL = os.environ.get("DATASERVICE_URL", "http://dataservice")

# The url of the Release Coordinator API
COORDINATOR_URL = os.environ.get(
    "COORDINATOR_URL", "https://kf-release-coord.kidsfirstdrc.org/graphql"
)


# LOGGING ######################################################################
# The Study Creator can store logs in S3 for asynchronous tasks performed by its
# workers

# The bucket where logs will be kept
LOG_BUCKET = os.environ.get("LOG_BUCKET", "kf-study-creator-logging")
# The relative path to the directory where job logs will be stored within the
# log bucket
LOG_DIR = os.environ.get("LOG_DIR", "logs/")
