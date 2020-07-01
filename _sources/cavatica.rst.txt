Cavatica Integration
====================

The Study Creator may integrate with Cavatica to automate the setup of new
projects for bioinformatics work.

Feature Flags
-------------

The Cavatica integration features may enabled with the following feature flags.

.. py:data:: FEAT_CAVATICA_CREATE_PROJECTS

    Create new projects in Cavatica when new studies are created

.. py:data:: FEAT_CAVATICA_COPY_USERS

   New analysis projects created by the study creator will have users copied
   over from a template project supplied by the
   :py:data:`CAVATICA_USER_ACCESS_PROJECT` setting.

.. py:data:: FEAT_CAVATICA_MOUNT_VOLUMES

   New Cavatica projects will have the study's bucket attached as a volume
   upon creation.

Configuration Settings
----------------------

The following settings need to be provided in order for the Cavatica
integration to function correctly.

.. py:data:: CAVATICA_URL

    **default:** ``https://cavatica-api.sbgenomics.com/v2``

    The url of the Cavatica api endpoint

.. py:data:: CAVATICA_HARMONIZATION_ACCOUNT

    **required**

    The username for the Cavatica account associated with the token given by
    :py:data:`CAVATICA_HARMONIZATION_TOKEN`.

.. py:data:: CAVATICA_HARMONIZATION_TOKEN

    **required**

    The api token for the harmonization Cavatica account

.. py:data:: CAVATICA_DELIVERY_ACCOUNT

    **required**

    The username for the Cavatica account associated with the token given by
    :py:data:`CAVATICA_DELIVERY_TOKEN`.

.. py:data:: CAVATICA_DELIVERY_TOKEN

    **required**

    The api token for the delivery Cavatica account

.. py:data:: CAVATICA_DEFAULT_WORKFLOWS

    **default:** Empty string

    **example:** ``bwa-mem gatk-haplotypecaller``

    A space separated list of the workflow projects to set up for a new study

.. py:data:: CAVATICA_USER_ACCESS_PROJECT

    **default:** ``kids-first-drc/user-access``

    The project_id of a Cavatica project which contains users and permissions
    that will be copied over to new Cavatica analysis projects.

.. py:data:: CAVATICA_READ_ACCESS_KEY

    **default:** ``None``

    The AWS access key for a read-only user with priviledges for the study
    buckets.

.. py:data:: CAVATICA_READ_SECRET_KEY

    **default:** ``None``

    The AWS secret key for a read-only user with priviledges for the study
    buckets.

.. py:data:: CAVATICA_READWRITE_ACCESS_KEY

    **default:** ``None``

    The AWS access key for a user with priviledges for the study buckets.

.. py:data:: CAVATICA_READWRITE_SECRET_KEY

    **default:** ``None``

    The AWS secret key for a user with priviledges for the study buckets.


Configuration
-------------

To utilize the Cavatica features, the Study Creator needs to be provided with
Cavatica developer tokens.
To get a Cavatica token, log in / sign up into `Cavatica
<https://cavatica.sbgenomics.com/developer#token/>`_ , and navigate to the
developer page.
Export the token under :py:data:`CAVATICA_HARMONIZATION_TOKEN` and
:py:data:`CAVATICA_DELIVERY_TOKEN` in the Study Creator's environment to
allow it to utilize the tokens to communicate with Cavatic.
These settings may also take different tokens, if each project type should
utilize different Cavatica accounts.


Operation
---------

When a new study is created via the `createStudy` mutation, the Study Creator
will work with Cavatica to set up new projects for future bioinformatics work.
This includes:
- Specifying a standard project id format
- Naming the project based on the Study's name
- Copying the description from that of the study's
- Creating harmonization projects for each desired workflow

Cavatica Accounts
-----------------

The Study Creator creates two different kinds of projects: harmonization and
delivery.
It offers the ability to create each type within its own distinct account by
providing :py:data:`CAVATICA_HARMONIZATION_TOKEN` and
:py:data:`CAVATICA_DELIVERY_TOKEN` settings.
If the separation of the two projects types is not needed, both settings may
be configured to share the same token.

Synchronizing Projects
----------------------

The Study Creator provides the `syncProjects` mutation which will iterate all
projects for *both cavatica tokens* and ensure that all the projects within
the Study Creator exist and are up to date.
This is a purely passive operation meaning that no data will be updated in
Cavatica, only in the Study Creator's view of the projects.

Volume Mounting
---------------

A bucket will be created for new studies as part of the study creation flow
given that :py:data:`FEAT_BUCKETSERVICE_CREATE_BUCKETS` is enabled.
This bucket may optionally be added as a volume during the study creation flow
by enabling :py:data:`FEAT_CAVATICA_MOUNT_VOLUMES` and providing S3
credentials in the configuration given with
the :py:data:`CAVATICA_READWRITE_ACCESS_KEY` and
:py:data:`CAVATICA_READWRITE_SECRET_KEY` key-pair.

The new Cavatica volume will be added to the account of the token given by
:py:data:`CAVATICA_HARMONIZATION_TOKEN` with full privileges and the account
specified by :py:data:`CAVATICA_DELIVERY_ACCOUNT` will be added as a user with
read and copy permissions.
