import sys
import pytest
from importlib import reload, import_module
from django.urls.base import clear_url_caches


@pytest.fixture
def reload_urls():
    """
    Needed in order to re-evaluate the root url configuration which
    depends on values in the settings
    """

    def f(settings):
        clear_url_caches()
        urlconf = settings.ROOT_URLCONF
        if urlconf in sys.modules:
            reload(sys.modules[urlconf])
        else:
            import_module(urlconf)

    yield f


@pytest.fixture
def dev_endpoints(settings, reload_urls):
    settings.DEVELOPMENT_ENDPOINTS = True
    reload_urls(settings)
