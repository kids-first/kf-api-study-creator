.. _dev_api:

Development API
===============

The development API adds endpoints to simplify actions needed to change
database state without having to restart the entire application.
The endpoints may be enabled with the :py:data:`DEVELOPMENT_ENDPOINTS` setting.

Configuration Settings
----------------------

The development API needs to be explicitly enabled through settings.
The API should not be enabled in any deployed scenarios.

.. py:data:: DEVELOPMENT_ENDPOINTS

    **default:** ``False``

    Whether to mount the development endpoints

Endpoints
---------

.. http:post:: /__dev/reset-db/

    Restores the database to the original state with pre-populated test data

.. http:post:: /__dev/change-groups/

    Modifies the permission groups on `testuser`

    :query groups: The names of the groups to add the user to separated by `,`.
        Not including this parameter will clear all groups from the user.
