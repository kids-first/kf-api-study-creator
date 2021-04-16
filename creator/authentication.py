import requests
import logging
from typing import Dict, Optional
from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)


def client_headers(aud: str) -> Dict[str, str]:
    """
    Get a m2m token from Auth0 and return a dictionary to be passed as headers
    containing the authorization field and any other fields.
    """
    cache_key = f"ACCESS_TOKEN:{aud}"
    token = cache.get_or_set(
        cache_key, lambda: get_token(aud), settings.CACHE_AUTH0_TIMEOUT
    )

    headers = settings.REQUESTS_HEADERS
    if token:
        headers.update({"Authorization": "Bearer " + token})
    return headers


def get_token(aud: str) -> Optional[str]:
    """
    Retrieve a token for a given audience from Auth0.

    The study creator application in Auth0 as specified by the AUTH0_CLIENT
    must have permission to use the API corresponding to the given aud or else
    it will fail to retrieve a token.
    """
    if (
        settings.AUTH0_CLIENT is None
        or settings.AUTH0_SECRET is None
        or aud is None
    ):
        logger.warning(
            "There is insufficient configuration available to retrieve a "
            "m2m token. "
            "Requests may be sent without an Authorization header"
        )
        return

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
