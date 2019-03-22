import logging
import json
import jwt
import re
import requests
import textwrap
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.auth.middleware import get_user
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class EgoJWTAuthenticationMiddleware():
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only attempt to resolve if user has not yet been extracted
        if not request.user.is_authenticated:
            request.user = self.__class__.get_jwt_user(request)
        return self.get_response(request)

    @staticmethod
    def get_jwt_user(request):
        """
        Creates a user object from the JWT in the Authorization header.
        This user object will be used to grant permissions based on their
        groups and roles.
        If no valid token is found, an anonymous user will be returned

        If running with the DEVELOP = True setting, all requests will be
        treated as requests from an admin to grant permission to all data
        """
        if settings.DEVELOP:
            # Assume user is admin if running in dev mode
            return get_user_model()(
                    ego_groups=[],
                    ego_roles=['ADMIN'])

        user = request.user
        if user.is_authenticated:
            return user

        encoded = request.META.get('HTTP_AUTHORIZATION')
        if not encoded:
            return AnonymousUser()
        encoded = encoded.replace('Bearer ', '')

        try:
            # Validate JWT using Ego's public key
            public_key = EgoJWTAuthenticationMiddleware._get_ego_key()
            token = jwt.decode(encoded, public_key, algorithms='RS256',
                               options={'verify_aud': False})
        except jwt.exceptions.DecodeError as err:
            logger.error(f'Problem authenticating request: {err}')
            return AnonymousUser()
        except jwt.exceptions.InvalidTokenError as err:
            logger.error(f'Token provided is not valid: {err}')
            return AnonymousUser()

        if not('context' in token and 'user' in token['context']):
            return AnonymousUser()

        user_context = token['context']['user']
        groups = user_context['groups']
        roles = user_context['roles']

        user = get_user_model()(
                ego_groups=groups,
                ego_roles=roles)

        return user

    @staticmethod
    def _get_ego_key():
        """
        Attempts to retrieve the ego public key from the cache. If it's not
        there or is expired, fetch a new one from ego and store it back in the
        cache.
        """
        key = cache.get(settings.CACHE_EGO_KEY, None)
        # If key is not set in cache (or has timed out), get a new one
        if key is None:
            key = EgoJWTAuthenticationMiddleware._get_new_key()
            cache.set(settings.CACHE_EGO_KEY, key, settings.CACHE_EGO_TIMEOUT)
        return key

    @staticmethod
    def _get_new_key():
        """
        Get a public key from ego

        We reformat the keystring as the whitespace is not always consistent
        with the pem format
        """
        resp = requests.get(f'{settings.EGO_API}/oauth/token/public_key',
                            timeout=10)
        key = resp.content
        key = key.replace(b'\n', b'')
        key = key.replace(b'\r', b'')
        key_re = r'-----BEGIN PUBLIC KEY-----(.*)-----END PUBLIC KEY-----'
        contents = re.match(key_re, key.decode('utf-8')).group(1)
        contents = '\n'.join(textwrap.wrap(contents, width=65))
        contents = f'\n{contents}\n'
        key = f'-----BEGIN PUBLIC KEY-----{contents}-----END PUBLIC KEY-----'
        key = key.encode()
        return key


class Auth0AuthenticationMiddleware():
    """
    Authentication middleware for validating a user's identity through Auth0
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only attempt to resolve if user has not yet been extracted
        if not request.user.is_authenticated:
            request.user = self.__class__.get_jwt_user(request)
        return self.get_response(request)

    @staticmethod
    def get_jwt_user(request):
        """
        Creates a user object from the JWT in the Authorization header.
        This user object will be used to grant permissions based on their
        groups and roles.
        If no valid token is found, an anonymous user will be returned

        If running with the DEVELOP = True setting, all requests will be
        treated as requests from an admin to grant permission to all data
        """
        if settings.DEVELOP:
            # Assume user is admin if running in dev mode
            return get_user_model()(
                    ego_groups=[],
                    ego_roles=['ADMIN'])

        user = request.user
        if user.is_authenticated:
            return user

        encoded = request.META.get('HTTP_AUTHORIZATION')
        if not encoded:
            return AnonymousUser()
        encoded = encoded.replace('Bearer ', '')

        try:
            # Validate JWT using the Auth0 key
            public_key = Auth0AuthenticationMiddleware._get_auth0_key()
            token = jwt.decode(encoded, public_key, algorithms='RS256',
                               audience=settings.AUTH0_AUD)
        except jwt.exceptions.DecodeError as err:
            logger.error(f'Problem authenticating request: {err}')
            return AnonymousUser()
        except jwt.exceptions.InvalidTokenError as err:
            logger.error(f'Token provided is not valid: {err}')
            return AnonymousUser()

        groups = token.get('https://kidsfirstdrc.org/groups')
        roles = token.get('https://kidsfirstdrc.org/roles')
        # Currently unused
        permissions = token.get('https://kidsfirstdrc.org/permissions')

        # Don't allow if it looks like the token doesn't have correct fields
        if groups is None or roles is None:
            return AnonymousUser()

        user = get_user_model()(
                ego_groups=groups,
                ego_roles=roles)

        return user

    @staticmethod
    def _get_auth0_key():
        """
        Attempts to retrieve the auth0 public key from the cache. If it's not
        there or is expired, fetch a new one from auth0 and store it back in
        the cache.
        """
        key = cache.get(settings.CACHE_AUTH0_KEY, None)
        # If key is not set in cache (or has timed out), get a new one
        if key is None:
            key = Auth0AuthenticationMiddleware._get_new_key()
            # Cache doesn't like the public key format
            # cache.set(settings.CACHE_AUTH0_KEY, key,
            #           settings.CACHE_AUTH0_TIMEOUT)
        return key

    @staticmethod
    def _get_new_key():
        """
        Get a public key from Auth0 jwks
        """
        resp = requests.get(settings.AUTH0_JWKS, timeout=10)
        key = resp.json()['keys'][0]
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
        return public_key
