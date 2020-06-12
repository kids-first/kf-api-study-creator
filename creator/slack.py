import logging
import datetime
import re
from django.conf import settings
from django.utils import timezone
from collections import defaultdict
from slack import WebClient
from creator.studies.models import Study

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


def summary_post():
    """
    This will post recent events to a study's Slack channel
    """
    studies = Study.objects.all()

    today = timezone.now()
    yesterday = today - datetime.timedelta(days=100)
    since = yesterday.strftime("%Y/%m/%d")

    def study_header(url, study_id, study_name):
        message = (
            f":file_cabinet: `{study_id}` *{study_name}*\n"
            f"Here is a summary of events since {since}"
        )
        return {
            "type": "section",
            "text": {"type": "mrkdwn", "text": message},
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "emoji": True,
                    "text": "View Study :file_cabinet:",
                },
                "url": url,
            },
        }

    def make_study_message(studyObj):
        """
        Make an event timeline for a study
        """
        blocks = []
        study_id = studyObj.kf_id
        study_name = studyObj.name

        # Get all events for a single study within previous 24 hours
        study_events = studyObj.events.filter(
            created_at__range=(yesterday, today)
        )

        # Collect and form all the events to slack messages
        new_doc = study_events.filter(event_type="SF_CRE").count()
        del_doc = study_events.filter(event_type="SF_DEL").count()
        upd_doc = study_events.filter(event_type="SF_UPD").count()
        add_col = study_events.filter(event_type="CB_ADD").count()
        rem_col = study_events.filter(event_type="CB_REM").count()
        new_doc_m = str(new_doc) + " new document(s) " if new_doc > 0 else ""
        del_doc_m = str(del_doc) + " new version(s) " if del_doc > 0 else ""
        upd_doc_m = (
            str(upd_doc) + " document update(s) " if upd_doc > 0 else ""
        )
        add_col_m = (
            str(add_col) + " collaborator(s) joined " if add_col > 0 else ""
        )
        rem_col_m = (
            str(rem_col) + " collaborator(s) removed " if rem_col > 0 else ""
        )
        file_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":file_folder: {new_doc_m + upd_doc_m + del_doc_m}",
            },
        }
        collaborator_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":male-technologist: {add_col_m + rem_col_m}",
            },
        }

        # Add header for slack message with study name and link
        if new_doc + del_doc + upd_doc + add_col + rem_col > 0:
            blocks.append(
                study_header(
                    f"{settings.DATA_TRACKER_URL}/study/{study_id}/documents"
                    "?utm_source=slack_daily_dm",
                    study_id,
                    study_name,
                )
            )

        # Add slack messages of files and collaborators updates
        if new_doc + del_doc + upd_doc > 0:
            blocks.append(file_block)
        if add_col + rem_col > 0:
            blocks.append(collaborator_block)

        return blocks

    filtered_studies = (
        studies.filter(slack_notify=True)
        .filter(slack_channel__isnull=False)
        .all()
    )

    logger.info(
        f"Posting slack messages to {len(filtered_studies)} studies"
        f" - updates since {since}"
    )
    client = WebClient(token=settings.SLACK_TOKEN)

    for study in filtered_studies:
        channel_id = study.slack_channel
        blocks = make_study_message(study)
        if len(blocks) > 0:
            response = client.channels_join(name=channel_id)

            response = client.chat_postMessage(
                channel=channel_id, blocks=blocks
            )

            # Should be caught by the slack client but we will check anyway
            if "ok" in response and not response["ok"]:
                logger.warn(f"Slack responded unexpectedly: {response}")

    return len(filtered_studies)
