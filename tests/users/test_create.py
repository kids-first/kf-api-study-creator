from django.contrib.auth import get_user_model


def test_new_auth0_user(client, token, db):
    """
    Test that a user is saved in the database upon first request with an Auth0
    token.
    """
    # Create an Auth0 token
    token = token(["ADMIN"], ["SD_ME0WME0W"])

    User = get_user_model()
    assert User.objects.count() == 0

    query = "{ allStudies { edges { node { name } } } }"
    resp = client.post(
        "/graphql",
        data={"query": query},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert User.objects.count() == 1
    user = User.objects.first()
    # Groups and roles should be empty, despite token containing them
    assert user.ego_groups == []
    assert user.ego_roles == []
    assert user.username == "bobby"
    assert user.email == "bobbytables@example.com"
    last_login = user.last_login

    resp = client.post(
        "/graphql",
        data={"query": query},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert User.objects.count() == 1
    user = User.objects.first()
    assert user.last_login > last_login
