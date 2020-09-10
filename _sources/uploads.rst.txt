Uploads
=======

An integral part of the Study Creator API is to accept and manage data
uploading.


New Document Uploads
--------------------

:ref:`Documents<Document>` are the central collections used to house one or
more :ref:`Versions<Version>` of file contents.
However, in order to create a Document, a first Version must already exist
as a prerequisite.
This is necessary so that the new Document's valid file types may be determined
by the contents of the Version.
The mutation flow for creating a new document is then:

- ``createVersion(file: Upload!, study: ID!)``
- ``createFile(version: ID!, description: String!, fileType: FileType!, name:
  String!)``

Upon creating a new Version, the contents will be analyzed which will inform
the valid possibilities to use for ``fileType`` when creating the Document.

Organization
------------

Files are uploaded into `S3` with a prefix of the form:

.. code-block:: bash

    {study_bucket}/source/uploads/

Uploading with GraphQL
----------------------
The upload request is expected to conform to the
`GraphQL multipart request spec <https://github.com/jaydenseric/graphql-multipart-request-spec>`_.

The contents of the mutation query would be:

.. code-block:: bash

    mutation ($file: Upload!, $studyId: ID!) {
      createVersion(file: $file, studyId: $studyId) {
        version {
            id
            kfId
            name
            downloadUrl
        }
      }
    }

But the ``createVersion`` mutation is sent as a single operation in a multipart
request and will need to be followed with a file.
See the examples below for how this works.

Curl example
^^^^^^^^^^^^
.. code-block:: bash

    curl localhost:5002/graphql \
      -F operations='{ "query": "mutation ($file: Upload!, $studyId: String!) { createVersion(file: $file, studyId: $studyId) { success } }", "variables": { "file": null, "studyId": <study kf id> } }' \
      -F map='{ "0": ["variables.file"] }' \
      -F 0=@<your filepath>

Python example
^^^^^^^^^^^^^^
.. code-block:: Python

    import json
    import requests
    from requests_toolbelt.multipart.encoder import MultipartEncoder

    query = '''
            mutation ($file: Upload!, $studyId: ID!) {
              createVersion(file: $file, studyId: $studyId) {
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
    response = requests.post('http://localhost:5002/graphql', data=m,
                             headers={'Content-Type': m.content_type})


New Version Uploads
-------------------

New Versions of a Document are uploaded in the same way while specifying the
document to which they belong:

.. code-block:: bash

    mutation ($file: Upload!, $fileId: String) {
      createVersion(file: $file, fileId: $fileId) {
        success
        version {
            kfId
        }
      }
    }
