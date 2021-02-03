def test_sentry_middleware(db, clients, mocker, settings):
    """
    Check that users are added to the Sentry context when the middleware
    is active.
    """
    settings.MIDDLEWARE.append("creator.middleware.SentryMiddleware")

    client = clients.get("Administrators")

    mock = mocker.patch("sentry_sdk.set_user")

    client.get("health_check")

    assert mock.call_count == 1


def test_sentry_middleware_no_user(db, clients, mocker, settings):
    """
    Test that no users are registered with Sentry when a request cannot be
    resolved to a user
    """
    settings.MIDDLEWARE.append("creator.middleware.SentryMiddleware")

    client = clients.get(None)

    mock = mocker.patch("sentry_sdk.set_user")

    client.get("health_check")

    assert mock.call_count == 0
