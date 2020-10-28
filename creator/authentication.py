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

    if token:
        headers = {"Authorization": "Bearer " + token}
        headers.update(settings.REQUESTS_HEADERS)
        return headers
    else:
        return {}


def get_service_token():
    """
    Get a new token from Auth0 so we can authenticate with our release services
    """
    logger.info(
        f"Try to get token from auth0 with "
        f"clientId={settings.AUTH0_CLIENT}, "
        f"audience={settings.AUTH0_SERVICE_AUD}, "
        f"domain ={settings.AUTH0_DOMAIN}"
    )
    url = f"{settings.AUTH0_DOMAIN}/oauth/token"
    headers = {"Content-Type": "application/json"}
    data = {
        "grant_type": "client_credentials",
        "client_id": settings.AUTH0_CLIENT,
        "client_secret": settings.AUTH0_SECRET,
        "audience": settings.AUTH0_SERVICE_AUD,
    }

    try:
        resp = requests.post(
            url, headers=headers, json=data, timeout=settings.REQUESTS_TIMEOUT
        )
        resp.raise_for_status()
        logger.info(f"Retrieved a new client_credentials token from Auth0")
    except requests.exceptions.RequestException as err:
        logger.error(f"Problem retrieving access token from Auth0: {err}")
        raise

    content = resp.json()

    if "access_token" not in content:
        logger.error(
            f"Recieved a malformed response for an access token from Auth0: "
            f"{resp.content}"
        )
        return

    token = content["access_token"]
    return token
