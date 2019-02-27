Uploads
=======

An integral part of the Study Creator API is to accept and manage data
uploading.

Organization
------------

Files are uploaded into `S3` with a prefix of the form:

.. code-block:: bash

    {study_bucket}/source/{batch}/

Uploading with GraphQL
----------------------
Use the ``createFile`` mutation to upload a file to a batch.

Curl example
^^^^^^^^^^^^
.. code-block:: bash

    curl localhost:8000/graphql \
      -F operations='{ "query": "mutation ($file: Upload!, $batchId: Int!) { createFile(file: $file, batchId: $batchId) { success } }", "variables": { "file": null, "batchId": <id> } }' \
      -F map='{ "0": ["variables.file"] }' \
      -F 0=@<your file name>
