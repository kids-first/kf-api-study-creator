.. _authentication:

Authentication
==============

The Study Creator API uses JWTs issued from Auth0 as its method of
authentication.
Also supported are JWTs created with the ``client_credentials`` grant for
Auth0 tokens to allow services to communicate with the API and to verify
outgoing requests from the Study Creator to other inegrations.

Request Verification
--------------------

The API will attempt to validate a request's ``Bearer`` token against the
public key found at ``https://kids-first.auth0.com/.well-known/jwks.json``.
The API will cache this key for some period of time so that it will not need
to be retrieved for every authenticated request.

Upon successfull validation, the user's ``roles``, ``groups``, and
``permissions`` will be read from the token's
``https://kidsfirstdrc.org/groups``, ``https://kidsfirstdrc.org/roles``,
and ``https://kidsfirstdrc.org/permissions`` claims.
If it is the first time this user has authenticated with the API, a request
will be made to fetch additional information about the user from Auth0 using
the ``/userinfo`` endpoint as decribed by the `OIDC UserInfo <https://openid.net/specs/openid-connect-core-1_0.html#UserInfo>`_
specification.
Once additional info has been retrieved from Auth0, the user's profile will be
saved to the database so that this query will not have to be made again.

See :ref:`auth0` for more details on how to set up the integration.

Service Tokens
--------------

Valid tokens with the ``client_credentials`` grant type will automatically be
given the ``ADMIN`` role, but they will not be saved to the database.
