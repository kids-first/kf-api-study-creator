Authorization
=============

Authorization is granted based on a user's ``roles`` and ``groups`` as provided
by their token.

Role Permissions
----------------

``ADMIN`` users will be allowed to perform all operations on all entities
in the API.

.. _user-types:

User Types
----------

Unauthenticated user
++++++++++++++++++++

Any requests that come with invalid or missing JWT header are considered
unauthenticated, and will not have access to any resources.

Authenticated user
++++++++++++++++++

Any request with a valid JWT header containing a ``groups`` context containing
a list of study ``kf_id`` to which the user belongs. The user will be allowed
to perform certain requests with these studies alone.

Admin user
++++++++++

Any request with a valid JWT header containing a ``roles`` context that has a
``ADMIN`` value. The user will be allowed to perform all actions and access all
resources.

Resource Permissions
--------------------

+------------------+-------------------------+-------------------------------+--------+
| Model            | Permission              | Description                   | Exists |
+==================+=========================+===============================+========+
| user             | add_user                | Can add user                  | yes    |
+------------------+-------------------------+-------------------------------+--------+
| user             | change_user             | Can change user               | yes    |
+------------------+-------------------------+-------------------------------+--------+
| user             | delete_user             | Can delete user               | yes    |
+------------------+-------------------------+-------------------------------+--------+
| user             | view_user               | Can view user                 | yes    |
+------------------+-------------------------+-------------------------------+--------+
| event            | add_event               | Can add event                 | yes    |
+------------------+-------------------------+-------------------------------+--------+
| event            | change_event            | Can change event              | yes    |
+------------------+-------------------------+-------------------------------+--------+
| event            | delete_event            | Can delete event              | yes    |
+------------------+-------------------------+-------------------------------+--------+
| event            | view_event              | Can view event                | yes    |
+------------------+-------------------------+-------------------------------+--------+
| devdownloadtoken | add_devdownloadtoken    | Can add dev download token    | yes    |
+------------------+-------------------------+-------------------------------+--------+
| devdownloadtoken | change_devdownloadtoken | Can change dev download token | yes    |
+------------------+-------------------------+-------------------------------+--------+
| devdownloadtoken | delete_devdownloadtoken | Can delete dev download token | yes    |
+------------------+-------------------------+-------------------------------+--------+
| devdownloadtoken | view_devdownloadtoken   | Can view dev download token   | yes    |
+------------------+-------------------------+-------------------------------+--------+
| downloadtoken    | add_downloadtoken       | Can add download token        | yes    |
+------------------+-------------------------+-------------------------------+--------+
| downloadtoken    | change_downloadtoken    | Can change download token     | yes    |
+------------------+-------------------------+-------------------------------+--------+
| downloadtoken    | delete_downloadtoken    | Can delete download token     | yes    |
+------------------+-------------------------+-------------------------------+--------+
| downloadtoken    | view_downloadtoken      | Can view download token       | yes    |
+------------------+-------------------------+-------------------------------+--------+
| file             | add_file                | Can add file                  | yes    |
+------------------+-------------------------+-------------------------------+--------+
| file             | change_file             | Can change file               | yes    |
+------------------+-------------------------+-------------------------------+--------+
| file             | delete_file             | Can delete file               | yes    |
+------------------+-------------------------+-------------------------------+--------+
| file             | view_file               | Can view file                 | yes    |
+------------------+-------------------------+-------------------------------+--------+
| version          | add_version             | Can add version               | yes    |
+------------------+-------------------------+-------------------------------+--------+
| version          | change_version          | Can change version            | yes    |
+------------------+-------------------------+-------------------------------+--------+
| version          | delete_version          | Can delete version            | yes    |
+------------------+-------------------------+-------------------------------+--------+
| version          | view_version            | Can view version              | yes    |
+------------------+-------------------------+-------------------------------+--------+
| project          | add_project             | Can add project               | yes    |
+------------------+-------------------------+-------------------------------+--------+
| project          | link_project            | Can link a project to a study | no     |
+------------------+-------------------------+-------------------------------+--------+
| project          | change_project          | Can change project            | yes    |
+------------------+-------------------------+-------------------------------+--------+
| project          | delete_project          | Can delete project            | yes    |
+------------------+-------------------------+-------------------------------+--------+
| project          | view_project            | Can view project              | yes    |
+------------------+-------------------------+-------------------------------+--------+
| study            | add_study               | Can add study                 | yes    |
+------------------+-------------------------+-------------------------------+--------+
| study            | change_study            | Can change study              | yes    |
+------------------+-------------------------+-------------------------------+--------+
| study            | delete_study            | Can delete study              | yes    |
+------------------+-------------------------+-------------------------------+--------+
| study            | view_study              | Can view study                | yes    |
+------------------+-------------------------+-------------------------------+--------+

Study Permissions
+++++++++++++++++

Studies must be created through the database directly. By default, studies from
the ``DATASERVICE`` will be synchronized on container start in deployment
environments.

Users are granted access to studies by adding study kf_ids to their 'groups'.

``USER`` Role Permissions
+++++++++++++++++++++++++

+----------+---------------+--------------------------------------------+
| Resource | Action        | Permission                                 |
+==========+===============+============================================+
| Study    | list          | Studies in GROUPS                          |
+----------+---------------+--------------------------------------------+
| Study    | create/update | Not allowed                                |
+----------+---------------+--------------------------------------------+
| Study    | delete        | Not allowed                                |
+----------+---------------+--------------------------------------------+
| File     | list          | Files of studies in GROUPS                 |
+----------+---------------+--------------------------------------------+
| File     | create/update | Files of studies in GROUPS                 |
+----------+---------------+--------------------------------------------+
| File     | delete        | Not allowed                                |
+----------+---------------+--------------------------------------------+
| Version  | list          | Versions of files of studies in GROUPS     |
+----------+---------------+--------------------------------------------+
| Version  | create/update | Versions of files of studies in GROUPS     |
+----------+---------------+--------------------------------------------+
| Version  | delete        | Not allowed                                |
+----------+---------------+--------------------------------------------+
| User     | list          | Only self                                  |
+----------+---------------+--------------------------------------------+
| User     | create/update | Not allowed                                |
+----------+---------------+--------------------------------------------+
| User     | delete        | Not allowed                                |
+----------+---------------+--------------------------------------------+
| Token    | list          | Not allowed                                |
+----------+---------------+--------------------------------------------+
| Token    | create/update | For versions of files of studies in GROUPS |
+----------+---------------+--------------------------------------------+
| Token    | delete        | Not allowed                                |
+----------+---------------+--------------------------------------------+
| DevToken | list          | Not allowed                                |
+----------+---------------+--------------------------------------------+
| DevToken | create/update | Not allowed                                |
+----------+---------------+--------------------------------------------+
| DevToken | delete        | Not allowed                                |
+----------+---------------+--------------------------------------------+

``ADMIN`` Role Permissions
++++++++++++++++++++++++++

+----------+---------------+-----------------------+
| Resource | Action        | Permission            |
+==========+===============+=======================+
| Study    | list          | All studies           |
+----------+---------------+-----------------------+
| Study    | create/update | Allowed               |
+----------+---------------+-----------------------+
| Study    | delete        | Not allowed           |
+----------+---------------+-----------------------+
| File     | list          | All files             |
+----------+---------------+-----------------------+
| File     | create/update | All files             |
+----------+---------------+-----------------------+
| File     | delete        | All files             |
+----------+---------------+-----------------------+
| Version  | list          | All versions          |
+----------+---------------+-----------------------+
| Version  | create/update | All versions          |
+----------+---------------+-----------------------+
| Version  | delete        | All versions          |
+----------+---------------+-----------------------+
| User     | list          | All users             |
+----------+---------------+-----------------------+
| User     | create/update | Not allowed           |
+----------+---------------+-----------------------+
| User     | delete        | Not allowed           |
+----------+---------------+-----------------------+
| Token    | list          | Not allowed           |
+----------+---------------+-----------------------+
| Token    | create/update | All files             |
+----------+---------------+-----------------------+
| Token    | delete        | Not allowed           |
+----------+---------------+-----------------------+
| DevToken | list          | All tokens, name only |
+----------+---------------+-----------------------+
| DevToken | create/update | Allowed               |
+----------+---------------+-----------------------+
| DevToken | delete        | Allowed               |
+----------+---------------+-----------------------+
