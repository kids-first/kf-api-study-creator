from promise import Promise
from promise.dataloader import DataLoader
from django.contrib.auth import get_user_model

User = get_user_model()


class UserLoader(DataLoader):
    """
    Data loader for user objects
    """

    def batch_load_fn(self, keys):
        results_by_id = {}

        for result in User.objects.filter(id__in=keys).all():
            results_by_id[result.id] = result
        return Promise.resolve([results_by_id.get(id, []) for id in keys])
