import requests
import logging
from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)


def service_headers():
    """ Construct headers for requests to release services """
    token = cache.get_or_set(
        settings.CACHE_AUTH0_SERVICE_KEY,
        get_service_token,
        settings.CACHE_AUTH0_TIMEOUT,
    )

    headers = settings.REQUESTS_HEADERS
    if token:
        headers.update({"Authorization": "Bearer " + token})
    return headers


def management_headers():
    """ Construct header fields for requests to the Auth0 management API """
    token = cache.get_or_set(
        settings.CACHE_AUTH0_MANAGEMNET_KEY,
        get_management_token,
        settings.CACHE_AUTH0_TIMEOUT,
    )

    headers = settings.REQUESTS_HEADERS
    if token:
        headers.update({"Authorization": "Bearer " + token})
    return headers


def get_token(aud):
    """
    Retrieve a token for a given audience from Auth0.

    The study creator application in Auth0 as specified by the AUTH0_CLIENT
    must have permission to use the API corresponding to the given aud or else
    it will fail to retrieve a token.
    """
    url = f"{settings.AUTH0_DOMAIN}/oauth/token"
    headers = {"Content-Type": "application/json"}
    data = {
        "grant_type": "client_credentials",
        "client_id": settings.AUTH0_CLIENT,
        "client_secret": settings.AUTH0_SECRET,
        "audience": aud,
    }

    try:
        resp = requests.post(
            url, headers=headers, json=data, timeout=settings.REQUESTS_TIMEOUT
        )
        resp.raise_for_status()
        logger.info(f"Retrieved a new client_credentials token from Auth0")
    except requests.exceptions.RequestException as err:
        logger.warning(
            f"Problem retrieving access token from Auth0: {err}. "
            f"Response: {getattr(err.response, 'content', '')}"
        )
        logger.warning(
            "An authentication token could not be retrieved. "
            "Requests may be sent without an Authorization header"
        )
        return

    content = resp.json()

    if "access_token" not in content:
        logger.warning(
            f"Recieved a malformed response for an access token from Auth0: "
            f"{resp.content}"
        )
        return

    token = content["access_token"]
    return token


def get_service_token():
    """
    Get a new token from Auth0 so we can authenticate with our release services
    """
    if (
        settings.AUTH0_CLIENT is None
        or settings.AUTH0_SECRET is None
        or settings.AUTH0_SERVICE_AUD is None
    ):
        logger.warning(
            "There is insufficient configuration available to retrieve a "
            "service token. "
            "Requests may be sent without an Authorization header"
        )
        return

    logger.info(
        f"There is no Auth0 token or it has expired. Will request a new one "
        f"for clientId={settings.AUTH0_CLIENT}"
    )
    return get_token(aud=settings.AUTH0_SERVICE_AUD)


def get_management_token():
    """
    Get a new management token for interacting with the Auth0 management API.
    """
    if (
        settings.AUTH0_CLIENT is None
        or settings.AUTH0_SECRET is None
        or settings.AUTH0_MANAGEMENT_AUD is None
    ):
        logger.warning(
            "There is insufficient configuration available to retrieve a "
            "management token. "
            "Requests may be sent without an Authorization header"
        )
        return

    logger.info(
        f"There is no Auth0 token or it has expired. Will request a new one "
        f"for clientId={settings.AUTH0_CLIENT}"
    )
    return get_token(aud=settings.AUTH0_MANAGEMENT_AUD)
