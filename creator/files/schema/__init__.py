import graphene
from django.db.utils import IntegrityError
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from .file import FileNode, FileQuery
from .version import VersionQuery

from ..models import File, Version, DownloadToken, DevDownloadToken


class DevDownloadTokenNode(DjangoObjectType):
    token = graphene.String()

    class Meta:
        model = DevDownloadToken
        interfaces = (relay.Node, )
        filter_fields = []

    def resolve_token(self, info):
        """
        Return an obscured token with only the first four characters exposed,
        unless the token is being returned in response to a new token mutation.
        """
        if info.path == ['createDevToken', 'token', 'token']:
            return self.token
        return self.token[:4] + '*' * (len(self.token) - 4)


class SignedUrlMutation(graphene.Mutation):
    """
    Generates a signed url and returns it
    """
    class Arguments:
        study_id = graphene.String(required=True)
        file_id = graphene.String(required=True)
        version_id = graphene.String(required=False)

    url = graphene.String()
    file = graphene.Field(FileNode)

    def mutate(self, info, study_id, file_id, version_id=None, **kwargs):
        """
        Generates a token for a signed url and returns a download url
        with the token inclueded as a url parameter.
        This url will be immediately usable to download the file one time.
        """
        user = info.context.user
        if ((user is None
             or not user.is_authenticated
             or study_id not in user.ego_groups
             and 'ADMIN' not in user.ego_roles)):
            return GraphQLError('Not authenticated to generate a url.')

        try:
            file = File.objects.get(kf_id=file_id)
        except File.DoesNotExist:
            return GraphQLError('No file exists with given ID')
        try:
            if version_id:
                version = file.versions.get(kf_id=version_id)
            else:
                version = file.versions.latest('created_at')
        except Version.DoesNotExist:
            return GraphQLError('No version exists with given ID')

        token = DownloadToken(root_version=version)
        token.save()

        url = f'{version.path}?token={token.token}'

        return SignedUrlMutation(url=url)


class DevDownloadTokenMutation(graphene.Mutation):
    """
    Generates a developer download token
    """
    class Arguments:
        name = graphene.String(required=True)

    token = graphene.Field(DevDownloadTokenNode)

    def mutate(self, info, name, **kwargs):
        """
        Generates a developer token with a given name.
        """
        user = info.context.user
        if ((user is None
             or not user.is_authenticated
             or 'ADMIN' not in user.ego_roles)):
            return GraphQLError('Not authenticated to generate a token.')

        token = DevDownloadToken(name=name, creator=user)
        try:
            token.save()
        except IntegrityError:
            return GraphQLError("Token with this name already exists.")

        return DevDownloadTokenMutation(token=token)


class DeleteDevDownloadTokenMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    success = graphene.Boolean()
    name = graphene.String()

    def mutate(self, info, name, **kwargs):
        """
        Deletes a developer download token by name
        """
        user = info.context.user
        if (user is None or
                not user.is_authenticated or
                'ADMIN' not in user.ego_roles):
            raise GraphQLError('Not authenticated to delete a token.')

        try:
            token = DevDownloadToken.objects.get(name=name)
        except DevDownloadToken.DoesNotExist:
            raise GraphQLError('Token does not exist.')

        token.delete()

        return DeleteDevDownloadTokenMutation(success=True, name=token.name)


class Query(FileQuery, VersionQuery):
    all_dev_tokens = DjangoFilterConnectionField(DevDownloadTokenNode)

    def resolve_all_dev_tokens(self, info, **kwargs):
        """
        If user is admin, return all tokens, otherwise return none
        """
        user = info.context.user

        if user is None or not user.is_authenticated:
            return DevDownloadToken.objects.none()

        if user.is_admin:
            return DevDownloadToken.objects.all()

        return DevDownloadToken.objects.none()
