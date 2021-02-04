from graphene_file_upload.django import FileUploadGraphQLView


class SentryGraphQLView(FileUploadGraphQLView):
    """
    Sets the Sentry transaction name to be that of the GraphQL operation.
    This helps break down all the /graphql requests into more actionable
    buckets within Sentry.
    """

    def execute_graphql_request(self, *args, **kwargs):
        """
        Attempt to extract the operation name and use it to set the Sentry
        transaction name.
        """

        # args[4] is the operationName, see super's signature:
        # https://github.com/graphql-python/graphene-django/blob/main/graphene_django/views.py#L278-L280
        if (
            args
            and len(args) >= 5
            and args[4] is not None
            and len(args[4]) > 0
        ):
            from sentry_sdk import Hub

            transaction = Hub.current.scope.transaction
            if transaction is not None:
                transaction.name = args[4]

        return super().execute_graphql_request(*args, **kwargs)
