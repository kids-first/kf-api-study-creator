from tabulate import tabulate
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Print permissions by group"

    def add_arguments(self, parser):
        parser.add_argument("-g", "--group", help="group to print", type=str)

    def handle(self, *args, **options):
        groups = None
        if options.get("group"):
            groups = Group.objects.filter(name=options.get("group")).all()
        else:
            groups = Group.objects.all()

        headers = ["Permission", "Description"]
        for group in groups:
            print(group)
            data = []
            for perm in group.permissions.all():
                data.append([perm.codename, perm.name])
            print(tabulate(data, headers=headers, tablefmt="rst"))
