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

    DEVELOP=True \
    DEVELOPMENT_ENDPOINTS=True \
    docker-compose \
        -f docker-compose.yml \
        -f docker-compose.dataservice.yml \
        -f docker-compose.coordinator.yml \
        -f docker-compose.email.yml \
        up -d


This will build and download necessary images and run them in development mode
with the primary webserver at ``http://localhost:5002``.
From here, the GraphiQL interface may be used to interact with the
pre-populated database of mock data.



.. toctree::
   :maxdepth: 2
   :caption: Development:

   development/quickstart
   model
   uploads
   downloads
   authentication
   authorization
   development/dev_api
   development/email

.. toctree::
   :maxdepth: 2
   :caption: Deployment:

   auth0
   bucketservice
   cavatica
   study_buckets
   dataservice
