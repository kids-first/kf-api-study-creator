import time
import logging
from django.core import management
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
