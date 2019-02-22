Uploads
=======

An integral part of the Study Creator API is to accept and manage data
uploading.

Organization
------------

Files are uploaded into `S3` with a prefix of the form:

.. code-block:: bash

    {study_bucket}/source/{batch}/
