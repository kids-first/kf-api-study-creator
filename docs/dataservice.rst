Data Service Integration
========================

The Study Creator may integrate with Cavatica to automate the setup of new
projects for bioinformatics work.

Feature Flags
-------------

The Cavatica integration features may enabled with the following feature flags.

.. py:data:: FEAT_DATASERVICE_CREATE_STUDIES

   New studies created in the Study Creator will be propagated to the
   Data Service

.. py:data:: FEAT_DATASERVICE_UPDATE_STUDIES

    Changes to existing studies in the Study Creator will be propagated to the
    Data Service.


Configuration Settings
----------------------

The Data Service integration requires these settings to be able to operate.

.. py:data:: DATASERVICE_URL

    **default:** ``https://dataservice``

    The url of the Data Service API


Operation
---------

When a new study is created via the ``createStudy`` mutation, the Study Creator
will first register the study in Data Service and allow Data Service to
generate a Kids First ID for the new study.
This study will then be stored with some additional fields internally in the
Study Creator.
Changes made to studies through the ``updateStudy`` mutation that affect fields
that are also stored in the Data Service will have changes propagated to the
Data Service, if the :py:data:`FEAT_DATASERVICE_UPDATE_STUDIES` flag is set.
