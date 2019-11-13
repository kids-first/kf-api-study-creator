.. _authentication:

Authentication
==============

The Study Creator API uses JWTs issued from either Ego or Auth0 as its method
of authentication.
Also supported are JWTs created with the ``client_credentials`` grant for
Auth0 tokens to allow services to communicate with the API.

Ego Authentication
------------------

The API will attempt to validate a request's ``Bearer`` token against the
public key found at the ``/oauth/token/public_key`` endpoint.
The API will cache these keys for some period of time so that it will not need
to be retrieved for every authenticated request.

Upon successfully validating a user for the first time, the user's profile
will be persisted to the database.

Auth0 Authentication
--------------------

The API will attempt to validate a request's ``Bearer`` token against the
public key found at ``https://kids-first.auth0.com/.well-known/jwks.json``.
The API will cache these keys for some period of time so that it will not need
to be retrieved for every authenticated request.

Upon successfull validation, the user's ``roles``, ``groups``, and
``permissions`` will be read from the token's
``https://kidsfirstdrc.org/groups``, ``https://kidsfirstdrc.org/roles``,
and ``https://kidsfirstdrc.org/permissions`` fields.
If it is the first time this user has authenticated with the API, a request
will be made to fetch additional information about the user from Auth0.
Once additional info has been retrieved from Auth0, the user's profile will be
saved to the database so that this query will not have to be made again.

Service Tokens
++++++++++++++

Valid tokens with the ``client_credentials`` grant type will automatically be
given the ``ADMIN`` role, but they will not be saved to the database.
