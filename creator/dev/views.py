import time
import logging
from django.core import management
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()
logger = logging.getLogger(__name__)


@csrf_exempt
def reset_db(request):
    """ Reset the database using the test seed """
    if not request.method == "POST":
        return JsonResponse(
            {"status": "fail", "message": "Only POST is supported"}
        )

    logger.info("Reseting database")
    t0 = time.time()
    management.call_command("flush", interactive=False)
    management.call_command("setup_permissions")
    management.call_command("setup_test_user")
    management.call_command("fakestudies", n=3, verbosity=0)
    management.call_command("fakefiles", verbosity=0)

    return JsonResponse({"status": "done", "took": time.time() - t0})


@csrf_exempt
def change_groups(request):
    """ Change permission groups of the test user"""
    if not request.method == "POST":
        return JsonResponse(
            {"status": "fail", "message": "Only POST is supported"}
        )

    logger.info("Changing test user groups")
    t0 = time.time()

    group_names = request.GET.get("groups", "").split(",")

    try:
        user = User.objects.get(username="testuser")
    except User.DoesNotExist:
        logger.info("User does not exist")
        return JsonResponse(
            {"status": "fail", "message": "Test user does not exist"}
        )

    if group_names == [""]:
        user.groups.clear()
        return JsonResponse({"status": "done", "took": time.time() - t0})

    groups = Group.objects.filter(name__in=group_names).all()
    if len(groups) != len(group_names):
        return JsonResponse(
            {
                "status": "fail",
                "message": "One or more of the groups were not found",
            }
        )
    user.groups.set(groups)
    user.save()

    return JsonResponse({"status": "done", "took": time.time() - t0})
