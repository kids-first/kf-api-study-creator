FILE_TYPES = {
    "OTH": {"name": "Other", "required_columns": [], "template": None},
    "SHM": {
        "name": "Shipping Manifest",
        "required_columns": [],
        "template": None,
    },
    "CLN": {"name": "Clinical Data", "required_columns": [], "template": None},
    "DBG": {
        "name": "dbGaP Submission File",
        "required_columns": [],
        "template": None,
    },
    "FAM": {
        "name": "Familial Relationships",
        "required_columns": [],
        "template": None,
    },
    "FCM": {
        "name": "Complex Family",
        "required_columns": [
            "First Participant ID",
            "Second Participant ID",
            "Relationship from First to Second"
        ],
        "template": "complex_family_config.py"
    },
    "FTR": {
        "name": "Family Trio",
        "required_columns": [
            "Participant ID",
            "Mother Participant ID",
            "Father Participant ID"
        ],
        "template": "family_trio_config.py"
    },
    "PDA": {
        "name": "Participant Details",
        "required_columns": [
            "Family ID",
            "Participant ID",
            "dbGaP Consent Code",
            "Clinical Sex",
            "Gender Identity",
            "Race",
            "Ethnicity",
            "Age at Study Enrollment Value",
            "Age at Study Enrollment Units",
            "Affected Status",
            "Proband",
            "Species",
            "Last Known Vital Status",
            "Age at Status Value",
            "Age at Status Units"
        ],
        "template": "participant_config.py"
    },
    "GOB": {
        "name": "General Observations",
        "required_columns": [
            "Participant ID",
            "Age at Observation Value",
            "Age at Observation Units",
            "Observation Name",
            "Observation Ontology Ontobee URI",
            "Observation Code",
            "Category",
            "Interpretation",
            "Status",
            "Body Site Name",
            "Body Site UBERON Code"
        ],
        "template": "general_observations_config.py"
    },
    "PTD": {
        "name": "Participant Diseases",
        "required_columns": [
            "Participant ID",
            "Age at Onset Value",
            "Age at Onset Units",
            "Age at Abatement Value",
            "Age at Abatement Units",
            "Condition Name",
            "Condition MONDO Code",
            "Verification Status",
            "Body Site Name",
            "Body Site UBERON Code",
            "Category"
        ],
        "template": "participant_diseases_config.py"
    },
    "PTP": {
        "name": "Participant Phenotypes",
        "required_columns": [
            "Participant ID",
            "Age at Onset Value",
            "Age at Onset Units",
            "Age at Abatement Value",
            "Age at Abatement Units",
            "Condition Name",
            "Condition HPO Code",
            "Verification Status",
            "Body Site Name",
            "Body Site UBERON Code"
        ],
        "template": "participant_phenotypes_config.py"
    },
    "ALM": {
        "name": "Aliquot Manifest",
        "required_columns": [
            "Specimen ID",
            "Aliquot ID",
            "Analyte Type",
            "Sequencing Center"
        ],
        "template": "aliquot_manifest_config.py",
    },
    "BBM": {
        "name": "Biobank Manifest",
        "required_columns": [
            "Specimen ID",
            "Aliquot ID",
            "Analyte Type",
            "Quantity Value",
            "Quantity Units",
            "Concentration Value",
            "Concentration Units",
            "Preservation Method",
            "Availability Status"
        ],
        "template": "biobank_manifest_config.py",

    },
    "BCM": {
        "name": "Biospecimen Collection Manifest",
        "required_columns": [
            "Participant ID",
            "Specimen ID",
            "Consent Short Name",
            "Consent Group",
            "Tissue Type Name",
            "Tissue Type NCIt Code",
            "Composition Name",
            "Composition SNOMED CT Code",
            "Body Site Name",
            "Body Site UBERON Code",
            "Age at Collection Value",
            "Age at Collection Units",
            "Method of Sample Procurement",
            "Ischemic Time",
            "Ischemic Units",
            "Origin Specimen ID",
            "Specimen Group ID"
        ],
        "template": "biospecimen_collection_manifest_config.py",
    },
    "SEQ": {
        "name": "Sequencing File Manifest",
        "required_columns": [
            "Aliquot ID",
            "Sequencing Output Filepath",
            "Sequencing Output File Hash",
            "File Hash Algorithm",
            "Reference Genome",
            "Experiment Strategy",
            "Experiment Date",
            "Sequencing Library Name",
            "Instrument Model",
            "Sequencing Platform",
            "Library Strand",
            "Library Selection",
            "Library Prep Kit",
            "Library BED File Download Link",
            "Is Paired End",
            "Expected Mean Insert Size",
            "Expected Mean Depth",
            "Expected Mean Read Length",
            "Expected Total Reads",
            "Quality Score System",
            "Quality Score Value"
        ],
        "template": "sequencing_manifest_config.py"
    },
    "S3S": {
        "name": "S3 Scrapes",
        "required_columns": ["Bucket", "Key", "Size", "ETag"],
        "template": "s3_scrape_config.py",
    },
    "GWO": {
        "name": "Genomic Workflow Output Manifest",
        "required_columns": [
            "Cavatica ID",
            "Cavatica Task ID",
            "KF Biospecimen ID",
            "KF Participant ID",
            "KF Family ID",
            "Filepath",
            "Data Type",
            "Workflow Type",
            "Source Read",
        ],
        "template": "genomic_workflow_output_manifest_config.py",
    },
}
