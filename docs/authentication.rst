Authentication
==============

The Study Creator API will use Ego tokens as its method of authentication.
A user will be allowed to add, view, and modify studies and files within them
based on their Ego role and groups.

Role Permissions
----------------

``ADMIN`` users will be allowed to perform all operations on all entities
in the API.

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

Study Permissions
+++++++++++++++++

Studies must be created through the database directly. By default, studies from
the ``DATASERVICE`` will be synchronized on container start in deployment
environments.

File Permissions
++++++++++++++++

Unauthenticated user:

  - May not view any files.
  - May not add any files.
  - May not modify any files.

Authenticated user:

  - May view files in their studies.
  - May upload files to their studies.
  - May modify files in their studies.

Admin user:

  - May view any file.
  - May upload file to any studies.
  - May modify any file.
