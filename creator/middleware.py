import jwt
from django.contrib.auth import get_user_model
from django.contrib.auth.middleware import get_user
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser


class EgoJWTAuthenticationMiddleware():
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = SimpleLazyObject(
                lambda: self.__class__.get_jwt_user(request)
        )
        return self.get_response(request)

    @staticmethod
    def get_jwt_user(request):
        user = get_user(request)
        if user.is_authenticated:
            return user

        encoded = request.META.get('HTTP_AUTHORIZATION')
        if not encoded:
            return AnonymousUser()
        encoded = encoded.replace('Bearer ', '')

        try:
            token = jwt.decode(str(encoded), verify=False)
        except jwt.exceptions.DecodeError:
            print('invalid auth')
        except jwt.exceptions.InvalidTokenError:
            print('problem decoding auth')

        if not('context' in token and 'user' in token['context']):
            return AnonymousUser()

        user_context = token['context']['user']
        groups = user_context['groups']
        roles = user_context['roles']

        user = get_user_model()(
                ego_groups=groups,
                ego_roles=roles)

        return user
