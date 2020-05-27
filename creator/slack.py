import logging
import logging
from django.conf import settings
from slack import WebClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def post_pin(client, study, channel_id):
    """ Post a descriptive message for the channel and pin it """
    message = f"{study.kf_id} - {study.name}"
    link = f"{settings.DATA_TRACKER_URL}/study/{study.kf_id}"
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*<{link}/basic-info/info|{study.kf_id}> "
                    f"- {study.name}*"
                ),
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": ":file_folder: Upload Files",
                    },
                    "url": f"{link}/documents",
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": ":cavatica: Manage Cavatica Projects",
                    },
                    "url": f"{link}/cavatica",
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": ":busts_in_silhouette: Add Collaborators",
                    },
                    "url": f"{link}/collaborators",
                },
            ],
        },
    ]

    response = client.chat_postMessage(
        channel=channel_id, text=message, blocks=blocks
    )

    timestamp = response["ts"]
    response = client.pins_add(channel=channel_id, timestamp=timestamp)


def invite_users(client, study, channel_id):
    """ Invite users to the new channel """
    # No users
    if settings.SLACK_USERS is None:
        return

    users = settings.SLACK_USERS
    response = client.conversations_invite(
        channel=channel_id, users=",".join(users)
    )

    logger.info(f"Invited {len(users)} to new channel for study {study.kf_id}")
    return response


def setup_slack(study):
    """
    Setup a Slack channel for the new study
    """
    client = WebClient(token=settings.SLACK_TOKEN)

    # Create channel
    name = study.kf_id.lower().replace("_", "-")
    response = client.conversations_create(name=name)
    channel_id = response["channel"]["id"]
    channel_name = response["channel"]["name"]
    # Update study with the slack channel's name
    study.slack_channel = channel_name
    study.save()

    # Set channel topic
    topic = f"`{study.kf_id}` - {study.name}"
    response = client.conversations_setTopic(channel=channel_id, topic=topic)

    # Pin a message to the new channel
    post_pin(client, study, channel_id)

    # Invite users to the new channel
    invite_users(client, study, channel_id)
