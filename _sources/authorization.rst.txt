Authorization
=============

Under the hood, the Study Creator uses `Django's permission model <https://docs.djangoproject.com/en/3.0/topics/auth/default/#permissions-and-authorization>`_
to grant access to different resources.
To summarize, entities have *permissions* which specify actions that may be
performed such as viewing a file, changing a study, or removing a project.
The *permissions* are not given directly to users but instead bundled together
into *groups* which may be assigned to users.
Users may have zero or more *groups* assigned to them.

Administrative users are automatically promoted on login based on their Auth0
identities, but all other user groups must be assigned to users by an existing
admin.

Roles
-----

The Study Creator has the concept of collaborator *roles* which are only
organizational and do not impact the abilities of the user.
The user's role in a study only specifies their function to be advertised to
others in the study.

Assigning User Groups
---------------------

Users are assigned one or more groups by an administrator.
Administrators are automatically assigned when they first login, however,
other users are not.
Users must exist in the Study Creator before being assigned groups meaning
that a user must login first before an administrator may assign them.

.. _user-types:

User Types
----------

Administators
+++++++++++++

These users have most permissions assigned to them.
Users may be assigned this group by another administrator or they will
automatically be promoted when logging in with an `ADMIN` role in their Auth0
token.

Developers
++++++++++

This user group works mostly with tokens and updating any status on data ETL.

Investigators
+++++++++++++

This group of users is focused on viewing their studies only and viewing and
uploading documents to them.

Bioinformatics
++++++++++++++

These users work most with Cavatica projects within studies.

Services
++++++++

This group is assigned to service users that access resources programatically.
They are usually concerned only with downloading files and generating tokens.
