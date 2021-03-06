.. _auth0:

Auth0 Integration
=================

The Study Creator integrates with Auth0 (or another OIDC serivce) to
authenticate users of the API.

See :ref:`authentication` for more information.

Feature Flags
-------------

Authentication will be performed by default so long as the Study Creator is
being run outside of ``DEBUG`` mode.
Otherwise, a default admin user will be used as the default authenticated
user for all requests.
This should only be used for local development needs.

Configuration Settings
----------------------

.. py:data:: AUTH0_DOMAIN

    **default:** ``https://kids-first.auth0.com``

    The base url for the OIDC complient endpoint.

.. py:data:: AUTH0_JKWS

    **required**

    **default** ``https://kids-first.auth0.com/.well-known/jwks.json``

    The endpoint from which to retriev a JWK to verify tokens being sent to
    the Study Creator as specified by the ``jwks_uri`` in the
    `OIDC Discovery configuration <https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderMetadata>`_
    of the auth provider.

.. py:data:: AUTH0_AUD

    **required**

    **default** ``https://kf-study-creator.kidsfirstdrc.org``

    The trusted audience of tokens which the Study Creator will accept.

.. py:data:: AUTH0_SERVICE_AUD

    **required**

    **default** ``https://kf-study-creator.kidsfirstdrc.org``

    The audience for which the Study Creator will retrieve
    ``client_credentials`` service tokens for.

.. py:data:: AUTH0_CLIENT

    **required**

    The client id for use in the ``client_credentials`` flow.

.. py:data:: AUTH0_SECRET

    **required**

    The client secret for use in the ``client_credentials`` flow.

.. py:data:: CACHE_AUTH0_KEY

    **default** ``AUTH0_PUBLIC_KEY``

    The key name to store the public key from :py:data:`AUTH0_JKWS` under in the
    cache.

.. py:data:: CACHE_AUTH0_SERVICE_KEY

    **default** ``AUTH0_SERVICE_KEY``

    The key name to store the service token retrieved from the
    ``client_credentials`` flow under in the cache.

.. py:data:: CACHE_AUTH0_TIMEOUT

    **default** ``86400``

    The time in seconds after which the :py:data:`CACHE_AUTH0_KEY` and
    :py:data:`CACHE_AUTH0_SERVICE_KEY` will expire and be refetched.


Configuration
-------------

The Study Creator will work with the auth provider to both to verify incoming
requests against the public key specified by :py:data:`AUTH0_JKWS` and
verify itself by attaching tokens with a ``client_credentials`` grant obtained
through the :py:data:`AUTH0_CLIENT` and :py:data:`AUTH0_SECRET` pair.
The verification of incoming tokens may be done by the Study Creator through
the public JWK endpoint as well as any other service that wishes to verify
them.

To verify outgoing requests by the Study Creator to external services, however,
require secrets to be stored to obtain tokens.
To do this, :py:data:`AUTH0_CLIENT` and :py:data:`AUTH0_SECRET` need to be
supplied in the environment.
These are generated by registering an application for the Study Creator in
Auth0 and registering a corresponding Auth0 API which allows Study Creator
application to access it.
The API's ``Identifier`` will be the ``aud`` used to request new
``client_credentials`` token and will need to be set for
:py:data:`AUTH0_SERVICE_AUD` so that the Study Creator may request the correct
``aud``.
See `How to implement the Client Credentials Grant <https://auth0.com/docs/api-auth/tutorials/client-credentials>`_
on Auth0 for more information.
