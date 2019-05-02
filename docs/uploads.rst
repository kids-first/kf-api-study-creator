Uploads
=======

An integral part of the Study Creator API is to accept and manage data
uploading.

Organization
------------

Files are uploaded into `S3` with a prefix of the form:

.. code-block:: bash

    {study_bucket}/source/uploads/

Uploading with GraphQL
----------------------
The upload request is expected to conform to the
`GraphQL multipart request spec <https://github.com/jaydenseric/graphql-multipart-request-spec>`_

Use the ``createFile`` mutation to upload a file to a study.

Curl example
^^^^^^^^^^^^
.. code-block:: bash

    curl localhost:8080/graphql \
      -F operations='{ "query": "mutation ($file: Upload!, $studyId: String!) { createFile(file: $file, studyId: $studyId) { success } }", "variables": { "file": null, "studyId": <study kf id> } }' \
      -F map='{ "0": ["variables.file"] }' \
      -F 0=@<your filepath>

Python example
^^^^^^^^^^^^^^
.. code-block:: Python

    import json
    import requests
    from requests_toolbelt.multipart.encoder import MultipartEncoder

    query = '''
            mutation ($file: Upload!, $studyId: String!) {
              createFile(file: $file, studyId: $studyId) {
                success
                file {
                    id
                    kfId
                    name
                    downloadUrl
                }
              }
            }
    '''

    m = MultipartEncoder(
        fields={
            'operations': json.dumps({
                'query': query.strip(),
                'variables': {
                    'file': None,
                    'studyId': study_kf_id
                }
            }),
            'map': json.dumps({
                '0': ['variables.file'],
            }),
            '0': ('foo.bar', open('foo.bar', 'rb'), 'text/plain')}
    )
    response = requests.post('http://localhost:8080/graphql', data=m,
                             headers={'Content-Type': m.content_type})


Uploading a New Version
-----------------------
To upload a new version of a file, use the `createFile` mutation as would be
done for creating the initial file and pass along the existing file's ``kfId``.
This will create a new version of the file under that root file, granted the
``kfId`` for the root file is correct.

Example mutation:

.. code-block:: bash

    mutation ($file: Upload!, $studyId: String!, $fileId: String) {
      createFile(file: $file, studyId: $studyId, fileId: $fileId) {
        success
        file {
            kfId
            versions { edges { node { kfId } } }
        }
      }
    }
