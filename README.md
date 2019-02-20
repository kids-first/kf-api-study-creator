<p align="center">
  <img src="docs/_static/images/study_creator.svg" alt="study creator logo" width="660px">
</p>
<p align="center">
  <a href="https://github.com/kids-first/kf-api-study-creator/blob/master/LICENSE"><img src="https://img.shields.io/github/license/kids-first/kf-api-study-creator.svg?style=for-the-badge"></a>
  <a href="https://kids-first.github.io/kf-api-study-creator/"><img src="https://img.shields.io/readthedocs/pip.svg?style=for-the-badge"></a>
  <a href="https://circleci.com/gh/kids-first/kf-api-study-creator"><img src="https://img.shields.io/circleci/project/github/kids-first/kf-api-study-creator.svg?style=for-the-badge"></a>
</p>

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

## Documentation

The below will build and auto-reload the documentation found within the
`docs/` directory:
```
sphinx-autobuild docs/ build -p 8000
```
