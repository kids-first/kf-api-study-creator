import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_endpoint(url):
    """Check that a url provided as an endpoint has expected format"""
    if not (url.startswith("http")):
        raise ValidationError(_("Enter a valid URL."))

    try:
        resp = requests.get(url + "/status", timeout=settings.REQUESTS_TIMEOUT)
        resp.raise_for_status()
        if resp.status_code != 200:
            raise ValueError("response did not return with 200")
        if "name" not in resp.json():
            raise ValueError("no 'name' in body")
    except requests.exceptions.RequestException as err:
        raise ValidationError(
            _("could not reach %(value)s: %(er)s"),
            params={"value": url, "er": str(err)},
        )
    except ValueError as err:
        raise ValidationError(
            _("%(val)s did not return the expected /status response: %(er)s"),
            params={"val": url, "er": str(err)},
        )
