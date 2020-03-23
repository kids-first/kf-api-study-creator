# This file contains the authorization groups and their contained permissions.
# It is to be used as the ground truth for determining what permissions each
# group has.

GROUPS = {
    "Administrators": [
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
    ],
    "Developers": [
        "view_downloadtoken",
        "add_downloadtoken",
        "delete_downloadtoken",
        "view_file",
        "view_version",
        "change_version",
    ],
    "Investigators": [
        "view_file",
        "list_all_file",
        "add_my_study_file",
        "change_my_study_file",
        "view_version",
        "add_my_study_version",
        "add_downloadtoken",
        "view_version",
        "change_version",
    ],
    "Bioinformatics": ["view_file", "add_downloadtoken"],
    "Services": ["add_file", "view_file"],
}
