from slack import WebClient
from django.conf import settings
from creator.releases.models import Release

state_emojis = {
    "waiting": ":clock1:",
    "initializing": ":cyclone:",
    "running": ":athletic_shoe:",
    "staged": ":warning:",
    "publishing": ":recycle:",
    "published": ":white_check_mark:",
    "canceling": ":double_vertical_bar:",
    "canceled": ":no_entry_sign:",
    "failed": ":exclamation:",
}


def send_status_notification(release_id):
    """
    Send a status notification to slack for the given release
    """
    release = Release.objects.get(pk=release_id)

    if settings.FEAT_SLACK_SEND_RELEASE_NOTIFICATIONS is False:
        return

    if release.state in ["waiting", "initializing"]:
        return

    client = WebClient(token=settings.SLACK_TOKEN)

    message = (
        f"🏷 *{release.kf_id}* ({release.version}) - {release.name} "
        f"\n{state_emojis.get(release.state)} The release is now "
        f"*{release.state}*"
    )

    blocks = []

    if release.state == "running":
        blocks.extend(release_header(release))

    state_block = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": message},
    }
    blocks.append(state_block)

    response = client.chat_postMessage(
        channel=settings.SLACK_RELEASE_CHANNEL, text=message, blocks=blocks
    )


def release_header(release):
    data_tracker_url = f"{settings.DATA_TRACKER_URL}"
    utm = "utm_source=slack_release_channel"
    release_url = f"{data_tracker_url}/releases/history/{release.pk}?{utm}"

    link_button = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*{release.name}*\n"},
        "accessory": {
            "type": "button",
            "text": {"type": "plain_text", "text": "Go to the Release Page"},
            "style": "primary",
            "url": release_url,
            "action_id": "button-action",
        },
    }
    description = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"{release.description}"},
    }

    studies = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                f"*There are {release.studies.count()} studies in this "
                "release:*\n"
            ),
        },
    }
    for study in release.studies.all():
        study_url = f"{data_tracker_url}/study/{study.kf_id}/basic-info/info"
        study_text = (
            f"`{study.kf_id}` - "
            f"<{study_url}|{study.short_name or study.name}>\n"
        )
        studies["text"]["text"] += study_text

    services = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                f"*There are {release.tasks.count()} services being run "
                "in this release:*\n"
            ),
        },
    }
    for task in release.tasks.all():
        service = task.release_service
        service_url = f"{data_tracker_url}/releases/services/{service.kf_id}"
        service_text = (
            f"`{service.kf_id}` - " f"<{service_url}|{service.name}>\n"
        )
        services["text"]["text"] += service_text

    return [link_button, description, studies, services]
