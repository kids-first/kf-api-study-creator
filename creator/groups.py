# This file contains the authorization groups and their contained permissions.
# It is to be used as the ground truth for determining what permissions each
# group has.

GROUPS = {
    "Administrators": [
        "view_study",
        "view_bucket",
        "list_all_bucket",
        "link_bucket",
        "unlink_bucket",
        "view_file",
        "add_file",
        "list_all_file",
        "change_file",
        "delete_file",
        "view_version",
        "add_version",
        "list_all_version",
        "change_version",
        "delete_version",
        "view_downloadtoken",
        "add_downloadtoken",
        "delete_downloadtoken",
        "list_all_user",
        "view_group",
        "view_permission",
        "view_event",
        "add_collaborator",
        "remove_collaborator",
    ],
    "Developers": [
        "view_study",
        "view_downloadtoken",
        "add_downloadtoken",
        "delete_downloadtoken",
        "view_file",
        "view_version",
        "change_version",
        "view_event",
    ],
    "Investigators": [
        "view_my_study",
        "view_my_file",
        "add_my_study_file",
        "change_my_study_file",
        "add_my_study_version",
        "add_downloadtoken",
        "view_my_version",
        "change_version",
        "view_my_event",
    ],
    "Bioinformatics": [
        "view_study",
        "view_file",
        "view_version",
        "add_downloadtoken",
        "view_event",
    ],
    "Services": ["view_study", "add_file", "view_file", "view_version"],
}
