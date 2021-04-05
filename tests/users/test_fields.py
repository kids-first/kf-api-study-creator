from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


def test_is_not_admin(db):
    """
    Test that users in the Administrators group are marked as admins
    """
    user = User(sub="abc")
    user.save()

    assert not user.is_admin


def test_is_admin(db):
    """
    Test that users in the Administrators group are marked as admins
    """
    user = User()
    user.save()

    admin_group = Group.objects.filter(name="Administrators").get()
    user.groups.add(admin_group)
    user.save()

    assert user.is_admin
