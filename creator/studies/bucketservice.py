import logging
import requests
from django.conf import settings
from django.core.cache import cache
from graphql import GraphQLError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def bucketservice_headers():
    """
    Construct request headers for bucket service interactions
    """
    headers = {
        "Authorization": "Bearer "
        + cache.get_or_set(
            settings.CACHE_AUTH0_SERVICE_KEY,
            get_service_token,
            settings.CACHE_AUTH0_TIMEOUT,
        )
    }
    headers.update(settings.REQUESTS_HEADERS)
    return headers


def get_service_token():
    """ Get a new token from Auth0 """
    url = f"{settings.AUTH0_DOMAIN}/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": settings.AUTH0_CLIENT,
        "client_secret": settings.AUTH0_SECRET,
        "audience": settings.AUTH0_SERVICE_AUD,
    }

    try:
        resp = requests.post(url, json=data, timeout=settings.REQUESTS_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.RequestException as err:
        logger.error(f"Problem retrieving access token from Auth0: {err}")
        raise GraphQLError(f"Problem authenticating self: {err}")

    content = resp.json()

    if "access_token" not in content:
        logger.error(f"Access token response malformed: {resp.content}")
        return

    token = content["access_token"]
    return token


def setup_bucket(study):
    """
    Calls the bucket service to create a bucket for a given study, then saves
    the resulting bucket's location to the study object.
    """
    logger.info(f"Setting up a bucket for {study.kf_id}")
    try:
        resp = requests.post(
            f"{settings.BUCKETSERVICE_URL}/buckets",
            json={"study_id": f"{study.kf_id}"},
            headers=bucketservice_headers(),
            timeout=settings.REQUESTS_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as err:
        logger.error(f"Problem calling the bucket service: {err}")
        raise GraphQLError(f"Problem calling the bucket service: {err}")
    logger.info(f"Bucket setup complete for {study.kf_id}")

    study.bucket = resp.json()["bucket"]

    return study
