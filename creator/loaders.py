from creator.studies.loaders import UserLoader


class Loaders:
    def __init__(self):
        self.user_loader = UserLoader(batch=True, max_batch_size=20)


class LoaderMiddleware:
    def resolve(self, next, root, info, **args):

        if not hasattr(info.context, "loaders"):
            info.context.loaders = Loaders()

        return next(root, info, **args)
