Development
===========

Enabling Cavatica Integration
-----------------------------

See :doc:`../cavatica` for enabling Cavatica features in the Study Creator.

Enabling Dataservice Features
-----------------------------

Creating new studies requires the study-creator to have access to the
dataservice.
This is not always possible or desirable as we often don't want test studies
being created in any of the live environments.
As an alternative, the dataservice may also be run in the local environment to
enable additional features.

.. code-block:: bash

    docker-compose -f docker-compose.yml -f docker-compose.dataservice.yml up -d

This will build and run a fresh dataservice container alongside the other
containers running in docker.
It will also enabled the dataservice features and configure them as needed
through the environment variables.


Bootstrapping the Database
--------------------------

It's often useful to have some data immediately available in the service
when developing and testing. By default, the container run through
``docker-compose`` will automatically populate the database with fake data
that has been randomly generated.

By changing the ``PRELOAD_DATA`` environment variable, this behavior can be
altered to a different strategy such as:

    - ``PRELOAD_DATA=FAKE`` to fill with random, fake data
    - ``PRELOAD_DATA=DATASERVICE`` to populated with data from the default
      dataservice (production)
    - ``PRELOAD_DATA=<dataservice_url>`` to use the dataservice at the given
      url to generate data
    - ``PRELOAD_DATA=<url to name of dataservice web docker container>`` to use
      your local dockerized dataservice (e.g. http://kf-api-dataservice_dataservice_1)
    - ``PRELOAD_DATA=false`` to start with an empty database

If you haven't already, create the kf-data-stack network. This is important
if you'd like to preload data from your dockerized dataservice.

.. code-block:: bash

    docker network create kf-data-stack

It may be required to restart the docker services after changing the
``PRELOAD_DATA`` environment variable so that the old data may be flushed.
Restart by running:

.. code-block:: bash

      PRELOAD_DATA=DATASERVICE docker-compose up


Testing
-------

It's suggested to run tests within the docker container to ensure that the
database and required services are running expectedly. This can be done with:

.. code-block:: bash

    docker-compose exec web pytest

Make sure that the docker compose is up first.


Developing Outside Docker
-------------------------

Although the code directory is mounted directly to the docker image and
the webserver running in debug mode to refresh on any code changes, there
may be some instances when development needs to happen outside of the
container.

To install and run in the local environment, it's suggested to use a virtual
environment as below:

.. code-block:: bash

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install -r dev-requirements.txt

It is again ideal to use docker to provide the database for development,
this time running it alone:

.. code-block:: bash

    docker run --name study-creator-pg -p 5432:5432 -d postgres:10.6

Although running postgres on the baremetal will work too.
The connection details for the database will then need to be altered either
on the docker postgres side or the bucket creator side. The bucket creator
can override its connection settings by changing the below to use the default
postgres settings:

.. code-block:: bash

    PG_NAME=postgres
    PG_USER=postgres
    PG_PASS=postgres
    PG_HOST=localhost
    PG_PORT=5432

Once these variables are in the environment, the new database will need to
be migrated using:

.. code-block:: bash

    python manage.py migrate

This will make sure the database has the latest schema. From here, tests
may be run with ``pytest`` and the development server started with
``python manage.py runserver``.


Settings
--------

There are three different settings files stored in `creator/settings/`:

- `development.py` - Used for local development, authenticates all requests as
  ``ADMIN`` user
- `testing.py` - Used for testing, default for docker-compose
- `production.py` - Used for production

To change which settings are being applied, set the `DJANGO_SETTINGS_MODULE`
variable to the settings module.
By default, the `creator.settings.production` settings will be used.

This setting may also be applied when running docker-compose, for example:

.. code-block:: bash

    DJANGO_SETTINGS_MODULE=creator.settings.development docker-compose up

Will run the api with development settings.


Authorization Overrides
-----------------------

When running in with the development settings, the default user's roles and
groups may be overridden for all requests.
This is done through the ``USER_ROLES`` and ``USER_GROUPS`` environment
variables.
For example:

.. code-block:: bash

    DJANGO_SETTINGS_MODULE=creator.settings.development USER_ROLES=ADMIN,DEV USER_GROUPS=SD_ABCABC12 docker-compose up

Will authenticate all requests as a user with the ``ADMIN`` and ``DEV`` roles
and as a member of the ``SD_ABCABC12`` group.
