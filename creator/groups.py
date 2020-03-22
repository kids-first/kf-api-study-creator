# This file contains the authorization groups and their contained permissions.
# It is to be used as the ground truth for determining what permissions each
# group has.

GROUPS = {
    "Administrators": [
        "view_bucket",
        "list_all_bucket",
        "link_bucket",
        "unlink_bucket",
        "list_all_user",
        "view_group",
        "view_permission",
    ],
    "Developers": [],
    "Investigators": [],
    "Bioinformatics": [],
    "Services": [],
}
