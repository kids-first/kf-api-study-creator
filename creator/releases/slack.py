from slack import WebClient
from django.conf import settings

state_emojis = {
    "initializing": ":clock1:",
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

    client = WebClient(token=settings.SLACK_TOKEN)

    data_tracker_url = f"{settings.DATA_TRACKER_URL}"
    release_url = f"{data_tracker_url}/releases/history/{release.pk}"

    message = (
        f"🏷 *{release.kf_id}* ({release.version}) - {release.name} "
        f"\n{state_emojis.get(release.state)} The release is now "
        f"*{release.state}*"
    )

    blocks = {
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message},
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Go to Release",
                        "emoji": false,
                    },
                    "style": "primary",
                    "url": release_url,
                    "action_id": "button-action",
                },
            }
        ]
    }

    response = client.chat_postMessage(
        channel=settings.SLACK_RELEASE_CHANNEL, text=message, blocks=blocks
    )
