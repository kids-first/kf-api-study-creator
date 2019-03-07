Development
===========

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
    - ``PRELOAD_DATA=false`` to start with an empty database

For example:

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
