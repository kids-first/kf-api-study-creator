.. _studybuckets:

Study Buckets Integration
=========================

The Study Creator manages S3 buckets in conjunction with the logistical
components of study creation and management.

Feature Flags
-------------

The study buckets integration features may enabled with the following feature
flags.

.. py:data:: FEAT_STUDY_BUCKETS_CREATE_BUCKETS

    Create a new study bucket when a new study is created


Configuration Settings
----------------------

The following settings need to be provided in order for the Cavatica
integration to function correctly.

.. py:data:: STUDY_BUCKETS_REGION

    The region in aws where new study buckets will be created

.. py:data:: STUDY_BUCKETS_LOGGING_BUCKET

    The bucket that access logs for new buckets will be sent to.

.. py:data:: STUDY_BUCKETS_DR_LOGGING_BUCKET

    The bucket that access logs for new data recovery buckets will be sent to.

.. py:data:: STUDY_BUCKETS_DR_REGION

    The region in aws where new replication buckets will be created

.. py:data:: STUDY_BUCKETS_INVENTORY_LOCATION

    The S3 location that bucket inventories will be stored in for new buckets.

.. py:data:: STUDY_BUCKETS_REPLICATION_ROLE

    The arn of the role to use for replication on new buckets.

.. py:data:: STUDY_BUCKETS_LOG_PREFIX

    The prefix where bucket logs will be stored in the logging buckets.

Operation
---------

When the :py:data:`FEAT_STUDY_BUCKETS_CREATE_BUCKETS` flag is enabled,
the Study Creator will allocate new S3 resources  during the `createStudy`
mutation to setup the necessary buckets for a study.
This will happen after the study has been created in the Data Service and
a new Kids First ID has been generated, but before creating new projects in
Cavatica.
