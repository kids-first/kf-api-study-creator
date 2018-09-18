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


### Organization 

Uploads should be stored within the `source/uploads/` prefix within the
relative study's bucket. Upon upload, the file's original name should be stored
in the `file_name` field in the dataservice data model, but should be renamed
to a UUID within s3 while preserving the extension. This prevents future
revisions from overwriting the file.

```
└── source
    └── uploads
        ├── 189b0888-4d5f-4849-ad55-6ffd70ca7ceb.csv
        └── 0acedaaf-e01d-4574-bccd-29f70d0a45d6.txt

```


### Versioning

Versions will likely be assisted through a ui that will differentiate between
adding a new file, and adding a new version. For near term, versions should
be tracked via a field in the dataservice (and/or indexd, file name).


### Visibility

The investigator should ultimately choose which files are intended for
redistribution. For the immediate case, only the files which are used to ingest
into the datamodel should be release, set to visible.


## Questions

Use of indexd dids/base ids for naming?

Versions in the file names?

How to determine when a file is a newer version of an existing file?

Store derived files?
