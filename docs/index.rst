Kids First Study Creator
========================

.. image:: /_static/images/study_creator.svg
   :alt: Kids First Study Creator

About
=====

The Study Creator is a GraphQL API backing the study creation process in
Kids First. It manages studies, batches, and the files within, allowing users
to version, validate, configure, and submit the data they are providing for
inclusion in Kids First.

Quickstart
----------

Getting started is easy! To start running instance of the service complete
with data, install
`Docker <https://www.docker.com>`_ and
`Docker Compose <https://docs.docker.com/compose/install>`_ then run:

.. code-block:: bash

    DJANGO_SETTINGS_MODULE=creator.settings.development docker-compose up --build -d


This will build and download necessary images and run them in development mode
with the primary webserver at ``http://localhost:8080``.
From here, the GraphiQL interface may be used to interact with the
pre-populated database of mock data.



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   development/quickstart
   model
   uploads
   downloads
   authentication
   authorization
