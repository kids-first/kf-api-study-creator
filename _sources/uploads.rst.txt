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

    curl localhost:8080/graphql \
      -F operations='{ "query": "mutation ($file: Upload!, $studyId: String!) { createFile(file: $file, studyId: $studyId) { success } }", "variables": { "file": null, "studyId": <study kf id> } }' \
      -F map='{ "0": ["variables.file"] }' \
      -F 0=@<your filepath>
