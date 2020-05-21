Authorization
=============

Under the hood, the Study Creator uses `Django's permission model <https://docs.djangoproject.com/en/3.0/topics/auth/default/#permissions-and-authorization>`_
to grant access to different resources.
Administrative users are automatically promoted on login based on their Auth0
identities, but all other user groups must be assigned to users by an existing
admin.

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

======================  ======================================
Permission              Description
======================  ======================================
view_group              Can view group
view_permission         Can view permission
link_bucket             Can link a bucket to a study
list_all_bucket         Can list all buckets
unlink_bucket           Can unlink a bucket to a study
view_bucket             Can view bucket
view_job                Can view job
view_queue              Can view queues
view_settings           Can view settings
change_user             Can change user
list_all_user           Can list all users
view_event              Can view event
list_all_version        Can list all versions
add_downloadtoken       Can add download token
delete_downloadtoken    Can delete download token
view_downloadtoken      Can view download token
add_file                Can add file
change_file             Can change file
delete_file             Can delete file
list_all_file           Can list all files
view_file               Can view file
add_version             Can add version
change_version          Can change version
delete_version          Can delete version
view_version            Can view version
add_project             Can add project
change_project          Can change project
import_volume           Can import a volume to a project
link_project            Can link a project to a study
list_all_project        Can list all projects
sync_project            Can sync projects with Cavatica
unlink_project          Can unlink a project from a study
view_project            Can view project
add_collaborator        Can add a collaborator to the study
add_study               Can add study
remove_collaborator     Can remove a collaborator to the study
view_study              Can view study
change_study            Can change study
view_referraltoken      Can view referral token
list_all_referraltoken  Can view all referral token
add_referraltoken       Can add referral token
======================  ======================================

Developers
++++++++++

This user group works mostly with tokens and updating any status on data ETL.

====================  =========================
Permission            Description
====================  =========================
view_event            Can view event
add_downloadtoken     Can add download token
delete_downloadtoken  Can delete download token
view_downloadtoken    Can view download token
view_file             Can view file
change_version        Can change version
view_version          Can view version
view_study            Can view study
====================  =========================

Investigators
+++++++++++++

This group of users is focused on viewing their studies only and viewing and
uploading documents to them.

=====================  ====================================================
Permission             Description
=====================  ====================================================
view_my_event          Can view all events in studies user is a member of
add_downloadtoken      Can add download token
add_my_study_file      Can add files to studies the user is a member of
change_my_study_file   Can change files in studies the user is a member of
view_my_file           Can view all files in studies user is a member of
add_my_study_version   Can add versions to studies the user is a member of
change_version         Can change version
view_my_version        Can view all versions in studies user is a member of
view_my_study_project  Can view projects in own studies
view_my_study          Can list studies that the user belongs to
=====================  ====================================================

Bioinformatics
++++++++++++++

These users work most with Cavatica projects within studies.

=================  =================================
Permission         Description
=================  =================================
view_event         Can view event
add_downloadtoken  Can add download token
view_file          Can view file
view_version       Can view version
add_project        Can add project
change_project     Can change project
import_volume      Can import a volume to a project
link_project       Can link a project to a study
list_all_project   Can list all projects
unlink_project     Can unlink a project from a study
view_project       Can view project
view_study         Can view study
=================  =================================

Services
++++++++

This group is assigned to service users that access resources programatically.
They are usually concerned only with downloading files and generating tokens.

============  ================
Permission    Description
============  ================
add_file      Can add file
view_file     Can view file
view_version  Can view version
view_study    Can view study
============  ================
