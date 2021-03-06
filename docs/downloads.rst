Downloads
=========

What good is an uploaded file if it cannot be retrieved?
The study creator authorizes download requests through role based permissions
and provides file downloads through two different mechanisms: typical JWT
authorization, and signed urls.

Role Authorization
------------------

There are three levels of file access following the three :ref:`user-types`.
Admin users are granted unrestricted access to download all files.
Authenticated users are restricted to downloading only files that are in a
study whose group the user belongs.
Unauthenticated users are not allowed to download any files.

Direct Download with Headers
----------------------------

To download a protected file using the standard JWT bearer tokens used
in the `GraphQL` endpoint, pass the same bearer token in the `Authorization`
header.

.. code-block:: bash

    curl -H "Authorization: Bearer $token" \
        /download/study/SD_00000000/file/SF_00000000

This endpoint is fairly deterministic and based on the following route:

.. code-block:: bash

    /download/study_id/<study_id>/file/<file_id>(?P/version/<version_id>)

Although this same url may be fetched from the file and version nodes as well:

.. code-block:: bash

    query fileUrls {
      allFiles {
        edges {
          node {
            downloadUrl
          }
        }
      }
    }

    query versionUrls {
      allVersions {
        edges {
          node{
            downloadUrl
          }
        }
      }
    }


Downloads with Signed Urls
--------------------------

Using the REST Endpoint
^^^^^^^^^^^^^^^^^^^^^^^

Signed urls allow files to be downloaded without any authorization headers.
This is important for allowing users to download from the browser, as it is
not possible to attach headers to requests made from anchor tags.

To initiate a download through a signed url, the client must send an authorized
request to the ``/signed-url`` endpoint:

.. code-block:: bash

    /study/<study_id>/files/<file_id>(?P/version/<version_id>)
    {
        "url": "/download/study/<study_id>/files/<file_id>/version/<version_id>?token=abc"
    }

The authorization used to generate a signed url is like any other download,
the only difference being that a url string is returned instead of a file.

This endpoint will respond with a json body containing a url.
This url is identical to the standard `downloadUrl`, except that it has an
additional token passed as a url parameter.
This token allows the file to be downloaded without additional authorization,
but it may only be claimed once and within a very short time period.
This protects against unauthorized sharing and re-use of the file download url.

Using a GraphQL Mutation
^^^^^^^^^^^^^^^^^^^^^^^^

Signed urls may also be obtained through the GraphQL API.

.. code-block:: bash

    mutation downloadURL {
      signedUrl(studyId: "SD_ME0WME0W", fileId: "SF_C9BCXNC8") {
        url
      }
    }

    {
      "data": {
        "signedUrl": {
          "url": "/download/study/SD_ME0WME0W/file/SF_C9BCXNC8/version/FV_TMMKQH14?token=lXuORIMbm0d6YzBcLQxR6FllouA"
        }
      }
    }

This mutation will return a url including the token that will allow the file
to be downloaded without further authorization.
The same authorization mechanisms are in place as in the REST endpoint.

Downloads with Developer Tokens
-------------------------------

There is a third option to download files using developer download tokens.
These tokens are similar to signed url tokens in that they may be passed as
a url parameter or under the `Authorization` header using a `Token`
prefix, although they are capable of downloading any file and do not expire.
Developer download tokens may only be generated by an admin user and should
be kept secret.
These tokens may also be generated or deleted an anytime, in case they are
accidentally distributed or no longer needed.
