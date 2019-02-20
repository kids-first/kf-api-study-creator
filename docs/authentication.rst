Authentication
==============

The Study Creator API will use Ego tokens as its method of authentication.
A user will be allowed to add, view, and modify studies and files within them
based on their Ego role and groups.

Role Permissions
----------------

``Admin`` users will be allowed to perform all operations on all entities
in the API.

Group Permissions
-----------------

Groups will be created for each study, using the study's ``kf_id`` for the
group's name. Users that belong to that group will be allowed to:

 - Create a batch in that study
 - Add files and versions in that study
 - Perform additional configuration of files in study's batches
 - Submit the batch for loading
