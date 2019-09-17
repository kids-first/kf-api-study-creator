Bucket Service Integration
==========================

The Study Creator may integrate with the
`Bucket Service <https://github.com/kids-first/kf-api-bucketservice>`_
to setup buckets for new studies.

Feature Flags
-------------

The Cavatica integration features may enabled with the following feature flags.

.. py:data:: FEAT_BUCKETSERVICE_CREATE_BUCKETS

    Create a new study bucket when a new study is created


Configuration Settings
----------------------

The following settings need to be provided in order for the Cavatica
integration to function correctly.

.. py:data:: BUCKETSERVICE_URL

    **default:** ``http://bucketservice``

    The url of the Bucket Service api endpoint


Operation
---------

When the :py:data`FEAT_BUCKETSERVICE_CREATE_BUCKETS` flag is enabled, the
Study Creator will make a call to the Bucket Service during the `createStudy`
mutation to setup the necessary bucket resources for a study.
This will happen after the study has been created in the Data Service and
a new Kids First ID has been generated, but before creating new projects in
Cavatica.
