"""
This file contains the datapackage in dict format that is converted to JSON
and included in each submission.
"""

DATAPACKAGE = {
    "profile": "tabular-data-package",
    "name": "table_schema_specs_for_c2m2_encoding_of_dcc_metadata",
    "title": "A complete list of schematic specifications for the resources (TSV table files) that will be used to represent C2M2 DCC metadata prior to ingest into the C2M2 database system",
    "resources": [
        {
            "profile": "tabular-data-resource",
            "name": "file",
            "title": "file",
            "path": "file.tsv",
            "description": "A stable digital asset",
            "schema": {
                "fields": [
                    {
                        "name": "id_namespace",
                        "description": "A CFDE-cleared identifier representing the top-level data space containing this file [part 1 of 2-component composite primary key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "local_id",
                        "description": "An identifier representing this file, unique within this id_namespace [part 2 of 2-component composite primary key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "project_id_namespace",
                        "description": "The id_namespace of the primary project within which this file was created [part 1 of 2-component composite foreign key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "project_local_id",
                        "description": "The local_id of the primary project within which this file was created [part 2 of 2-component composite foreign key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "persistent_id",
                        "description": "A persistent, resolvable (not necessarily retrievable) URI or compact ID permanently attached to this file",
                        "type": "string",
                    },
                    {
                        "name": "creation_time",
                        "description": "An ISO 8601 -- RFC 3339 (subset)-compliant timestamp documenting this file's creation time: YYYY-MM-DDTHH:MM:SS±NN:NN",
                        "type": "datetime",
                        "format": "any",
                    },
                    {
                        "name": "size_in_bytes",
                        "description": "The size of this file in bytes",
                        "type": "integer",
                    },
                    {
                        "name": "uncompressed_size_in_bytes",
                        "description": "The total decompressed size in bytes of the contents of this file",
                        "type": "integer",
                    },
                    {
                        "name": "sha256",
                        "description": "(preferred) SHA-256 checksum for this file [sha256, md5 cannot both be null]",
                        "type": "string",
                        "format": "binary",
                    },
                    {
                        "name": "md5",
                        "description": "(allowed) MD5 checksum for this file [sha256, md5 cannot both be null]",
                        "type": "string",
                        "format": "binary",
                    },
                    {
                        "name": "filename",
                        "description": "A filename with no prepended PATH information",
                        "type": "string",
                        "constraints": {"pattern": "^[^\/\\:]+$"},
                    },
                    {
                        "name": "file_format",
                        "description": "An EDAM CV term ID identifying the digital format of this file (e.g. TSV or FASTQ)",
                        "type": "string",
                        "constraints": {"pattern": "^format:[0-9]+$"},
                    },
                    {
                        "name": "data_type",
                        "description": "An EDAM CV term ID identifying the type of information stored in this file (e.g. RNA sequence reads)",
                        "type": "string",
                        "constraints": {"pattern": "^data:[0-9]+$"},
                    },
                    {
                        "name": "assay_type",
                        "description": "An OBI CV term ID describing the type of experiment that generated the results summarized by this file",
                        "type": "string",
                        "constraints": {"pattern": "^OBI:[0-9]+$"},
                    },
                    {
                        "name": "mime_type",
                        "description": "A MIME type describing this file",
                        "type": "string",
                    },
                ],
                "missingValues": [""],
                "primaryKey": ["id_namespace", "local_id"],
                "foreignKeys": [
                    {
                        "fields": ["project_id_namespace", "project_local_id"],
                        "reference": {
                            "resource": "project",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": "file_format",
                        "reference": {
                            "resource": "file_format",
                            "fields": "id",
                        },
                    },
                    {
                        "fields": "data_type",
                        "reference": {"resource": "data_type", "fields": "id"},
                    },
                    {
                        "fields": "assay_type",
                        "reference": {
                            "resource": "assay_type",
                            "fields": "id",
                        },
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "biosample",
            "title": "biosample",
            "path": "biosample.tsv",
            "description": "A tissue sample or other physical specimen",
            "schema": {
                "fields": [
                    {
                        "name": "id_namespace",
                        "description": "A CFDE-cleared identifier representing the top-level data space containing this biosample [part 1 of 2-component composite primary key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "local_id",
                        "description": "An identifier representing this biosample, unique within this id_namespace [part 2 of 2-component composite primary key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "project_id_namespace",
                        "description": "The id_namespace of the primary project within which this biosample was created [part 1 of 2-component composite foreign key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "project_local_id",
                        "description": "The local_id of the primary project within which this biosample was created [part 2 of 2-component composite foreign key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "persistent_id",
                        "description": "A persistent, resolvable (not necessarily retrievable) URI or compact ID permanently attached to this biosample",
                        "type": "string",
                    },
                    {
                        "name": "creation_time",
                        "description": "An ISO 8601 -- RFC 3339 (subset)-compliant timestamp documenting this biosample's creation time: YYYY-MM-DDTHH:MM:SS±NN:NN",
                        "type": "datetime",
                        "format": "any",
                    },
                    {
                        "name": "anatomy",
                        "description": "An UBERON CV term ID used to locate the origin of this biosample within the physiology of its source or host organism",
                        "type": "string",
                        "constraints": {"pattern": "^UBERON:[0-9]+$"},
                    },
                ],
                "missingValues": [""],
                "primaryKey": ["id_namespace", "local_id"],
                "foreignKeys": [
                    {
                        "fields": ["project_id_namespace", "project_local_id"],
                        "reference": {
                            "resource": "project",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": "anatomy",
                        "reference": {"resource": "anatomy", "fields": "id"},
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "subject",
            "title": "subject",
            "path": "subject.tsv",
            "description": "A biological entity from which a C2M2 biosample can be generated",
            "schema": {
                "fields": [
                    {
                        "name": "id_namespace",
                        "description": "A CFDE-cleared identifier representing the top-level data space containing this subject [part 1 of 2-component composite primary key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "local_id",
                        "description": "An identifier representing this subject, unique within this id_namespace [part 2 of 2-component composite primary key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "project_id_namespace",
                        "description": "The id_namespace of the primary project within which this subject was studied [part 1 of 2-component composite foreign key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "project_local_id",
                        "description": "The local_id of the primary project within which this subject was studied [part 2 of 2-component composite foreign key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "persistent_id",
                        "description": "A persistent, resolvable (not necessarily retrievable) URI or compact ID permanently attached to this subject",
                        "type": "string",
                    },
                    {
                        "name": "creation_time",
                        "description": "An ISO 8601 -- RFC 3339 (subset)-compliant timestamp documenting this subject record's creation time: YYYY-MM-DDTHH:MM:SS±NN:NN",
                        "type": "datetime",
                        "format": "any",
                    },
                    {
                        "name": "granularity",
                        "description": "A CFDE CV term categorizing this subject by multiplicity",
                        "type": "string",
                        "enum": [
                            "cfde_subject_granularity:0",
                            "cfde_subject_granularity:1",
                            "cfde_subject_granularity:2",
                            "cfde_subject_granularity:3",
                            "cfde_subject_granularity:4",
                            "cfde_subject_granularity:5",
                        ],
                        "constraints": {"required": True},
                    },
                ],
                "missingValues": [""],
                "primaryKey": ["id_namespace", "local_id"],
                "foreignKeys": [
                    {
                        "fields": ["project_id_namespace", "project_local_id"],
                        "reference": {
                            "resource": "project",
                            "fields": ["id_namespace", "local_id"],
                        },
                    }
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "primary_dcc_contact",
            "title": "primary_dcc_contact",
            "path": "primary_dcc_contact.tsv",
            "description": "One primary contact person for the Common Fund data coordinating center (DCC, identified by the given project foreign key) that produced this C2M2 instance",
            "schema": {
                "fields": [
                    {
                        "name": "contact_email",
                        "description": "Email address of this DCC contact",
                        "type": "string",
                        "format": "email",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "contact_name",
                        "description": "Name of this DCC contact",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "project_id_namespace",
                        "description": "The id_namespace of the project record representing this contact's DCC [part 1 of 2-component composite foreign key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "project_local_id",
                        "description": "The local_id of the project record representing this contact's DCC [part 2 of 2-component composite foreign key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "dcc_abbreviation",
                        "description": "A very short display label for this contact's DCC",
                        "type": "string",
                        "constraints": {"pattern": "^[a-zA-Z0-9_]+$"},
                    },
                    {
                        "name": "dcc_name",
                        "description": "A short, human-readable, machine-read-friendly label for this contact's DCC",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "dcc_description",
                        "description": "A human-readable description of this contact's DCC",
                        "type": "string",
                    },
                    {
                        "name": "dcc_url",
                        "description": "URL of the front page of the website for this contact's DCC",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                ],
                "missingValues": [""],
                "primaryKey": ["contact_email"],
                "foreignKeys": [
                    {
                        "fields": ["project_id_namespace", "project_local_id"],
                        "reference": {
                            "resource": "project",
                            "fields": ["id_namespace", "local_id"],
                        },
                    }
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "project",
            "title": "project",
            "path": "project.tsv",
            "description": "A node in the C2M2 project hierarchy subdividing all resources described by this DCC's C2M2 metadata",
            "schema": {
                "fields": [
                    {
                        "name": "id_namespace",
                        "description": "A CFDE-cleared identifier representing the top-level data space containing this project [part 1 of 2-component composite primary key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "local_id",
                        "description": "An identifier representing this project, unique within this id_namespace [part 2 of 2-component composite primary key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "persistent_id",
                        "description": "A persistent, resolvable (not necessarily retrievable) URI or compact ID permanently attached to this project",
                        "type": "string",
                    },
                    {
                        "name": "creation_time",
                        "description": "An ISO 8601 -- RFC 3339 (subset)-compliant timestamp documenting this project's creation time: YYYY-MM-DDTHH:MM:SS±NN:NN",
                        "type": "datetime",
                        "format": "any",
                    },
                    {
                        "name": "abbreviation",
                        "description": "A very short display label for this project",
                        "type": "string",
                        "constraints": {"pattern": "^[a-zA-Z0-9_]+$"},
                    },
                    {
                        "name": "name",
                        "description": "A short, human-readable, machine-read-friendly label for this project",
                        "type": "string",
                    },
                    {
                        "name": "description",
                        "description": "A human-readable description of this project",
                        "type": "string",
                    },
                ],
                "missingValues": [""],
                "primaryKey": ["id_namespace", "local_id"],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "project_in_project",
            "title": "project_in_project",
            "path": "project_in_project.tsv",
            "description": "Association between a child project and its parent",
            "schema": {
                "fields": [
                    {
                        "name": "parent_project_id_namespace",
                        "description": "ID of the identifier namespace for the parent in this parent-child project pair",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "parent_project_local_id",
                        "description": "The ID of the containing (parent) project",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "child_project_id_namespace",
                        "description": "ID of the identifier namespace for the child in this parent-child project pair",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "child_project_local_id",
                        "description": "The ID of the contained (child) project",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                ],
                "primaryKey": [
                    "parent_project_id_namespace",
                    "parent_project_local_id",
                    "child_project_id_namespace",
                    "child_project_local_id",
                ],
                "foreignKeys": [
                    {
                        "fields": [
                            "parent_project_id_namespace",
                            "parent_project_local_id",
                        ],
                        "reference": {
                            "resource": "project",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": [
                            "child_project_id_namespace",
                            "child_project_local_id",
                        ],
                        "reference": {
                            "resource": "project",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "collection",
            "title": "collection",
            "path": "collection.tsv",
            "description": "A grouping of C2M2 files, biosamples and/or subjects",
            "schema": {
                "fields": [
                    {
                        "name": "id_namespace",
                        "description": "A CFDE-cleared identifier representing the top-level data space containing this collection [part 1 of 2-component composite primary key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "local_id",
                        "description": "An identifier representing this collection, unique within this id_namespace [part 2 of 2-component composite primary key]",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "persistent_id",
                        "description": "A persistent, resolvable (not necessarily retrievable) URI or compact ID permanently attached to this collection",
                        "type": "string",
                    },
                    {
                        "name": "creation_time",
                        "description": "An ISO 8601 -- RFC 3339 (subset)-compliant timestamp documenting this collection's creation time: YYYY-MM-DDTHH:MM:SS±NN:NN",
                        "type": "datetime",
                        "format": "any",
                    },
                    {
                        "name": "abbreviation",
                        "description": "A very short display label for this collection",
                        "type": "string",
                        "constraints": {"pattern": "^[a-zA-Z0-9_]+$"},
                    },
                    {
                        "name": "name",
                        "description": "A short, human-readable, machine-read-friendly label for this collection",
                        "type": "string",
                    },
                    {
                        "name": "description",
                        "description": "A human-readable description of this collection",
                        "type": "string",
                    },
                ],
                "missingValues": [""],
                "primaryKey": ["id_namespace", "local_id"],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "collection_in_collection",
            "title": "collection_in_collection",
            "path": "collection_in_collection.tsv",
            "description": "Association between a containing collection (superset) and a contained collection (subset)",
            "schema": {
                "fields": [
                    {
                        "name": "superset_collection_id_namespace",
                        "description": "ID of the identifier namespace corresponding to the top-level C2M2 metadataset containing the superset collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "superset_collection_local_id",
                        "description": "The ID of the superset collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "subset_collection_id_namespace",
                        "description": "ID of the identifier namespace corresponding to the top-level C2M2 metadataset containing the subset collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "subset_collection_local_id",
                        "description": "The ID of the subset collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                ],
                "primaryKey": [
                    "superset_collection_id_namespace",
                    "superset_collection_local_id",
                    "subset_collection_id_namespace",
                    "subset_collection_local_id",
                ],
                "foreignKeys": [
                    {
                        "fields": [
                            "superset_collection_id_namespace",
                            "superset_collection_local_id",
                        ],
                        "reference": {
                            "resource": "collection",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": [
                            "subset_collection_id_namespace",
                            "subset_collection_local_id",
                        ],
                        "reference": {
                            "resource": "collection",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "collection_defined_by_project",
            "title": "collection_defined_by_project",
            "path": "collection_defined_by_project.tsv",
            "description": "(Shallow) association between a collection and a project that defined it",
            "schema": {
                "fields": [
                    {
                        "name": "collection_id_namespace",
                        "description": "ID of the identifier namespace corresponding to the top-level C2M2 metadataset containing this collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "collection_local_id",
                        "description": "The ID of this collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "project_id_namespace",
                        "description": "ID of the identifier namespace corresponding to the top-level C2M2 metadataset containing this project",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "project_local_id",
                        "description": "The ID of this project",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                ],
                "primaryKey": [
                    "collection_id_namespace",
                    "collection_local_id",
                    "project_id_namespace",
                    "project_local_id",
                ],
                "foreignKeys": [
                    {
                        "fields": [
                            "collection_id_namespace",
                            "collection_local_id",
                        ],
                        "reference": {
                            "resource": "collection",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": ["project_id_namespace", "project_local_id"],
                        "reference": {
                            "resource": "project",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "file_in_collection",
            "title": "file_in_collection",
            "path": "file_in_collection.tsv",
            "description": "Association between a file and a (containing) collection",
            "schema": {
                "fields": [
                    {
                        "name": "file_id_namespace",
                        "description": "Identifier namespace for this file",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "file_local_id",
                        "description": "The ID of this file",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "collection_id_namespace",
                        "description": "Identifier namespace for this collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "collection_local_id",
                        "description": "The ID of this collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                ],
                "primaryKey": [
                    "file_id_namespace",
                    "file_local_id",
                    "collection_id_namespace",
                    "collection_local_id",
                ],
                "foreignKeys": [
                    {
                        "fields": ["file_id_namespace", "file_local_id"],
                        "reference": {
                            "resource": "file",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": [
                            "collection_id_namespace",
                            "collection_local_id",
                        ],
                        "reference": {
                            "resource": "collection",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "biosample_in_collection",
            "title": "biosample_in_collection",
            "path": "biosample_in_collection.tsv",
            "description": "Association between a biosample and a (containing) collection",
            "schema": {
                "fields": [
                    {
                        "name": "biosample_id_namespace",
                        "description": "Identifier namespace for this biosample",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "biosample_local_id",
                        "description": "The ID of this biosample",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "collection_id_namespace",
                        "description": "Identifier namespace for this collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "collection_local_id",
                        "description": "The ID of this collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                ],
                "primaryKey": [
                    "biosample_id_namespace",
                    "biosample_local_id",
                    "collection_id_namespace",
                    "collection_local_id",
                ],
                "foreignKeys": [
                    {
                        "fields": [
                            "biosample_id_namespace",
                            "biosample_local_id",
                        ],
                        "reference": {
                            "resource": "biosample",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": [
                            "collection_id_namespace",
                            "collection_local_id",
                        ],
                        "reference": {
                            "resource": "collection",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "subject_in_collection",
            "title": "subject_in_collection",
            "path": "subject_in_collection.tsv",
            "description": "Association between a subject and a (containing) collection",
            "schema": {
                "fields": [
                    {
                        "name": "subject_id_namespace",
                        "description": "Identifier namespace for this subject",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "subject_local_id",
                        "description": "The ID of this subject",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "collection_id_namespace",
                        "description": "Identifier namespace for this collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "collection_local_id",
                        "description": "The ID of this collection",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                ],
                "primaryKey": [
                    "subject_id_namespace",
                    "subject_local_id",
                    "collection_id_namespace",
                    "collection_local_id",
                ],
                "foreignKeys": [
                    {
                        "fields": ["subject_id_namespace", "subject_local_id"],
                        "reference": {
                            "resource": "subject",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": [
                            "collection_id_namespace",
                            "collection_local_id",
                        ],
                        "reference": {
                            "resource": "collection",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "file_describes_biosample",
            "title": "file_describes_biosample",
            "path": "file_describes_biosample.tsv",
            "description": "Association between a biosample and a file containing information about that biosample",
            "schema": {
                "fields": [
                    {
                        "name": "file_id_namespace",
                        "description": "Identifier namespace for this file",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "file_local_id",
                        "description": "The ID of this file",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "biosample_id_namespace",
                        "description": "Identifier namespace for this biosample",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "biosample_local_id",
                        "description": "The ID of this biosample",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                ],
                "primaryKey": [
                    "file_id_namespace",
                    "file_local_id",
                    "biosample_id_namespace",
                    "biosample_local_id",
                ],
                "foreignKeys": [
                    {
                        "fields": ["file_id_namespace", "file_local_id"],
                        "reference": {
                            "resource": "file",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": [
                            "biosample_id_namespace",
                            "biosample_local_id",
                        ],
                        "reference": {
                            "resource": "biosample",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "file_describes_subject",
            "title": "file_describes_subject",
            "path": "file_describes_subject.tsv",
            "description": "Association between a subject and a file containing information about that subject",
            "schema": {
                "fields": [
                    {
                        "name": "file_id_namespace",
                        "description": "Identifier namespace for this file",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "file_local_id",
                        "description": "The ID of this file",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "subject_id_namespace",
                        "description": "Identifier namespace for this subject",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "subject_local_id",
                        "description": "The ID of this subject",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                ],
                "primaryKey": [
                    "file_id_namespace",
                    "file_local_id",
                    "subject_id_namespace",
                    "subject_local_id",
                ],
                "foreignKeys": [
                    {
                        "fields": ["file_id_namespace", "file_local_id"],
                        "reference": {
                            "resource": "file",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": ["subject_id_namespace", "subject_local_id"],
                        "reference": {
                            "resource": "subject",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "biosample_from_subject",
            "title": "biosample_from_subject",
            "path": "biosample_from_subject.tsv",
            "description": "Association between a biosample and its source subject",
            "schema": {
                "fields": [
                    {
                        "name": "biosample_id_namespace",
                        "description": "Identifier namespace for this biosample",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "biosample_local_id",
                        "description": "The ID of this biosample",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "subject_id_namespace",
                        "description": "Identifier namespace for this subject",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "subject_local_id",
                        "description": "The ID of this subject",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                ],
                "primaryKey": [
                    "biosample_id_namespace",
                    "biosample_local_id",
                    "subject_id_namespace",
                    "subject_local_id",
                ],
                "foreignKeys": [
                    {
                        "fields": [
                            "biosample_id_namespace",
                            "biosample_local_id",
                        ],
                        "reference": {
                            "resource": "biosample",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": ["subject_id_namespace", "subject_local_id"],
                        "reference": {
                            "resource": "subject",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "subject_role_taxonomy",
            "title": "subject_role_taxonomy",
            "path": "subject_role_taxonomy.tsv",
            "description": "Trinary association linking IDs representing (1) a subject, (2) a subject_role (a named organism-level constituent component of a subject, like 'host', 'pathogen', 'endosymbiont', 'taxon detected inside a microbiome subject', etc.) and (3) a taxonomic label (which is hereby assigned to this particular subject_role within this particular subject)",
            "schema": {
                "fields": [
                    {
                        "name": "subject_id_namespace",
                        "description": "Identifier namespace for this subject",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "subject_local_id",
                        "description": "The ID of this subject",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "role_id",
                        "description": "The ID of the role assigned to this organism-level constituent component of this subject",
                        "type": "string",
                        "enum": [
                            "cfde_subject_role:0",
                            "cfde_subject_role:1",
                            "cfde_subject_role:2",
                            "cfde_subject_role:3",
                            "cfde_subject_role:4",
                            "cfde_subject_role:5",
                            "cfde_subject_role:6",
                        ],
                        "constraints": {"required": True},
                    },
                    {
                        "name": "taxonomy_id",
                        "description": "An NCBI Taxonomy Database ID identifying this taxon",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                ],
                "primaryKey": [
                    "subject_id_namespace",
                    "subject_local_id",
                    "role_id",
                    "taxonomy_id",
                ],
                "foreignKeys": [
                    {
                        "fields": ["subject_id_namespace", "subject_local_id"],
                        "reference": {
                            "resource": "subject",
                            "fields": ["id_namespace", "local_id"],
                        },
                    },
                    {
                        "fields": "taxonomy_id",
                        "reference": {
                            "resource": "ncbi_taxonomy",
                            "fields": "id",
                        },
                    },
                ],
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "assay_type",
            "title": "assay_type",
            "path": "assay_type.tsv",
            "description": "List of Ontology for Biomedical Investigations (OBI) CV terms used to describe types of experiment that generate results stored in C2M2 files",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "description": "An OBI CV term",
                        "type": "string",
                        "constraints": {
                            "required": True,
                            "unique": True,
                            "pattern": "^OBI:[0-9]+$",
                        },
                    },
                    {
                        "name": "name",
                        "description": "A short, human-readable, machine-read-friendly label for this OBI term",
                        "type": "string",
                    },
                    {
                        "name": "description",
                        "description": "A human-readable description of this OBI term",
                        "type": "string",
                    },
                ],
                "missingValues": [""],
                "primaryKey": "id",
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "ncbi_taxonomy",
            "title": "ncbi_taxonomy",
            "path": "ncbi_taxonomy.tsv",
            "description": "List of NCBI Taxonomy Database IDs identifying taxa used to describe C2M2 subjects",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "description": "An NCBI Taxonomy Database ID identifying a particular taxon",
                        "type": "string",
                        "constraints": {
                            "required": True,
                            "unique": True,
                            "pattern": "^NCBI:txid[0-9]+$",
                        },
                    },
                    {
                        "name": "clade",
                        "description": "The phylogenetic level (e.g. species, genus) assigned to this taxon",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "name",
                        "description": "A short, human-readable, machine-read-friendly label for this taxon",
                        "type": "string",
                    },
                    {
                        "name": "description",
                        "description": "A human-readable description of this taxon",
                        "type": "string",
                    },
                ],
                "missingValues": [""],
                "primaryKey": "id",
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "anatomy",
            "title": "anatomy",
            "path": "anatomy.tsv",
            "description": "List of Uber-anatomy ontology (Uberon) CV terms used to locate the origin of a C2M2 biosample within the physiology of its source or host organism",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "description": "An Uberon CV term",
                        "type": "string",
                        "constraints": {
                            "required": True,
                            "unique": True,
                            "pattern": "^UBERON:[0-9]+$",
                        },
                    },
                    {
                        "name": "name",
                        "description": "A short, human-readable, machine-read-friendly label for this Uberon term",
                        "type": "string",
                    },
                    {
                        "name": "description",
                        "description": "A human-readable description of this Uberon term",
                        "type": "string",
                    },
                ],
                "missingValues": [""],
                "primaryKey": "id",
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "file_format",
            "title": "file_format",
            "path": "file_format.tsv",
            "description": "List of EDAM CV 'format:' terms used to describe formats of C2M2 files",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "description": "An EDAM CV format term",
                        "type": "string",
                        "constraints": {
                            "required": True,
                            "unique": True,
                            "pattern": "^format:[0-9]+$",
                        },
                    },
                    {
                        "name": "name",
                        "description": "A short, human-readable, machine-read-friendly label for this EDAM format term",
                        "type": "string",
                    },
                    {
                        "name": "description",
                        "description": "A human-readable description of this EDAM format term",
                        "type": "string",
                    },
                ],
                "missingValues": [""],
                "primaryKey": "id",
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "data_type",
            "title": "data_type",
            "path": "data_type.tsv",
            "description": "List of EDAM CV 'data:' terms used to describe data in C2M2 files",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "description": "An EDAM CV data term",
                        "type": "string",
                        "constraints": {
                            "required": True,
                            "unique": True,
                            "pattern": "^data:[0-9]+$",
                        },
                    },
                    {
                        "name": "name",
                        "description": "A short, human-readable, machine-read-friendly label for this EDAM data term",
                        "type": "string",
                    },
                    {
                        "name": "description",
                        "description": "A human-readable description of this EDAM data term",
                        "type": "string",
                    },
                ],
                "missingValues": [""],
                "primaryKey": "id",
            },
        },
        {
            "profile": "tabular-data-resource",
            "name": "id_namespace",
            "title": "id_namespace",
            "path": "id_namespace.tsv",
            "description": "A table listing identifier namespaces registered by the DCC submitting this C2M2 instance",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "description": "ID of this identifier namespace",
                        "type": "string",
                        "constraints": {"required": True},
                    },
                    {
                        "name": "abbreviation",
                        "description": "A very short display label for this identifier namespace",
                        "type": "string",
                        "constraints": {"pattern": "^[a-zA-Z0-9_]+$"},
                    },
                    {
                        "name": "name",
                        "description": "A short, human-readable, machine-read-friendly label for this identifier namespace",
                        "type": "string",
                    },
                    {
                        "name": "description",
                        "description": "A human-readable description of this identifier namespace",
                        "type": "string",
                    },
                ],
                "missingValues": [""],
                "primaryKey": "id",
            },
        },
    ],
}
