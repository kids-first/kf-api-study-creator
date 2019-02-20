# Kids First Study Creator

Create studies and upload files for ingestion into the Kids First datamodel.

## Development Quick Start

To get started developing, bring up the service with docker compose:
```
docker-compose up
```

Some mock data will automatically be loaded upon starting for immediate use
of the api.

The graphql endpoint and GraphiQL interface is available at
http://localhost:8080/graphql

Data may also be added and modified through the Django admin dashboard.
A Django superuser will be created with username `admin` and password `admin`.
You can log in to the admin dashboard at http://localhost:8080/admin.
