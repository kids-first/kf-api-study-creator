# Study Creator File uploads

## Motivation

The study creator exists to manage logistics around ground-truth data files.
These files are recieved from investigators, and often have many follow up
versions and patches.

## Requirements

Study files should:

- Land in a study's bucket in s3 after being uploaded
- Have conventions around organization and naming
- Have conventions around versioning
- Be immediatly registered in the dataservice
- Be made non-visible in the dateservice by default
- Exposed for automated ingestion
- Be tagged with the study id acl


### What are Study Files

Study files are files that are contributed by a study investigator containing
data inteded to be ingested to the Kids First data model.
A study file may be original files uploaded by the investigator, or original
files that have been slightly modified under the direction of the investigator
or someone familiar with the data.

Files that have been modified to accomodate etl, are the result of etl, or are
somehow derived from the original files should not be considered study files
and should not be uploaded.
These files are instead the responsibility of whatever etl process is
generating or consuming them.
They should live in a bucket dedicated to the etl service itself, if it has
been generalized for all studies, or within a different directory of the
study bucket if they are one-off.


### Organization 

Uploads should be stored within the `source/uploads/` prefix within the
relative study's bucket. Upon upload, the file's original name should be stored
in the `file_name` field in the dataservice data model, but should be renamed
to the latest_did UUID given by indexd.

```
└── source
    └── uploads
        ├── 189b0888-4d5f-4849-ad55-6ffd70ca7ceb.csv
        └── 0acedaaf-e01d-4574-bccd-29f70d0a45d6.txt
```


### Versioning

There will be no 'versioning' of files utilizing the version feature of indexd.
All previous files, however, will be kept but will be marked with a flag
indicating that the file has since been removed from the study and ingestion.
This will be done as to:

- Not break ingestion. Current ingestion configurations should be executable
despite not having been updated to the later files
- Maintain historical data for tracing and auditing
- Not complicate logistics around referencing the files in historical releases


### Visibility

The investigator should ultimately choose which files are intended for
redistribution by modifying the `visible` flag.
This will make that file part of the release and thus searchable on the portal
and discoverable in archives of that release in which it was visible.
Files that have been removed from the study, though they will still exist,
will not be included in any further releases.

### Working with Study Files

Because study files are required to be registered in the dataservice,
and the fact that files often need to be retrieved based on conditions on
some set of metadata, a user wishing to discover study files should go first
to the dataservice.
Although a user may refer to the file directly through its url, it may be
wise to occasionally look at the metadata in the dataservice to ensure that
the file is still valid (eg: a file has since been removed).
