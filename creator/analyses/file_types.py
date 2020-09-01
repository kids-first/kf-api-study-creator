FILE_TYPES = {
    "OTH": {"name": "Other", "required_columns": []},
    "SEQ": {"name": "Sequencing Manifest", "required_columns": []},
    "SHM": {"name": "Shipping Manifest", "required_columns": []},
    "CLN": {"name": "Clinical Data", "required_columns": []},
    "DBG": {"name": "dbGaP Submission File", "required_columns": []},
    "FAM": {"name": "Familial Relationships", "required_columns": []},
    "S3S": {
        "name": "S3 Scrapes",
        "required_columns": ["Bucket", "Key", "Size", "ETag"],
    },
}
