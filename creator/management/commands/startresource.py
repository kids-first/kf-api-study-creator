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
        resource_template = os.path.join(kwargs["template"], "resource")
        tests_template = os.path.join(kwargs["template"], "tests")

        if kwargs["directory"] is None:
            resource_target = os.path.join("creator", kwargs["name"])
            tests_target = os.path.join("tests", kwargs["name"])
        else:
            resource_target = os.path.join(kwargs["directory"], kwargs["name"])
            tests_target = os.path.join(kwargs["directory"], "tests")

        if kwargs["plural"] is None:
            kwargs["plural"] = kwargs["name"]

        # Try to derive the singular as best we can
        if kwargs["singular"] is None:
            if kwargs["name"].endswith("s"):
                kwargs["singular"] = kwargs["name"][:-1]

        # Inject some handy naming styles for use by the templates
        kwargs["uppercase"] = kwargs["singular"].upper()
        kwargs["uppercase_plural"] = kwargs["plural"].upper()

        os.makedirs(resource_target)
        os.makedirs(tests_target)

        del kwargs["directory"]
        del kwargs["template"]
        super().handle(
            "app",
            *args,
            target=resource_target,
            directory=resource_target,
            template=resource_template,
            **kwargs,
        )
        super().handle(
            "app",
            *args,
            target=tests_target,
            directory=tests_target,
            template=tests_template,
            **kwargs,
        )

        self.stdout.write(
            f"🎉 Created new app {kwargs['name']}.\n"
            "The application is not quite ready yet. Finalize it by doing the "
            "following:"
            "\n  1) Add app to INSTALLED_APPS in settings files"
            "\n  2) Add schema to top level `schema.py`"
            "\n  3) Modify models.py and run `manage.py makemigrations`"
            "\n  4) Add permissions for new resource in `groups.py`"
            "\n  5) Modify tests for appropriate permissions"
        )
