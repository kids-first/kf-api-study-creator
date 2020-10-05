import os
from django.core.management.templates import TemplateCommand


class Command(TemplateCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--model_name", help="The name of the ORM model")
        parser.add_argument(
            "--plural", help="The plural name of the resource. (snake case)"
        )
        parser.add_argument(
            "--singular",
            help="The singular name of the resource. (snake case)",
        )

    def handle(self, *args, **kwargs):
        os.makedirs(kwargs["directory"])

        if kwargs["plural"] is None:
            kwargs["plural"] = kwargs["name"]

        # Try to derive the singular as best we can
        if kwargs["singular"] is None:
            if kwargs["name"].endswith("s"):
                kwargs["singular"] = kwargs["name"][:-1]

        super().handle("app", *args, target=kwargs["directory"], **kwargs)

        self.stdout.write(
            "Created new app. \n Make sure to install it in the settings "
            "files, add it to the root schema, run migrations, and add "
            "permission groups."
        )
