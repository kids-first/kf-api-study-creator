"""
The application's default set of data templates

These are currently only used to support the Flatfile Portal import on the
frontend. Later on they may also be used to validate files that belong to a
study with no templates.
"""

default_templates = [
    {
        "template_name": "Participant Details",
        "template_description": (
            "This file should have one row per participant that contains"
            " demographic, vital status, and administrative information about"
            " the participant. The most important field in this file is the"
            " Participant ID and which will be used throughout the study for"
            " linkage and access control of data. "
        ),
        "fields": [
            {
                "key": "FAMILY|ID",
                "label": "Family ID",
                "required": False,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that describes a related group of"
                    " individuals, to which the participant belongs."
                ),
                "instructions": None,
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": "PARTICIPANT|ID",
                "label": "Participant ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified research identifier that is unique for each"
                    " participant. This identifier must follow the"
                    " https://www.ncbi.nlm.nih.gov/gap/docs/submissionguide/#6-what-do-i-need-to-know-about-p"
                    " of dbGaP."
                ),
                "instructions": (
                    "A unique string per participant within the study."
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "dbGaP Consent Code",
                "required": False,
                "data_type": "string",
                "description": (
                    "Indicate which data use limitation, as indicated on the"
                    " provided Institutional Certification, is associated with"
                    " each participant"
                ),
                "instructions": (
                    "Consent codes as defined by institutional certification"
                    " with dbGaP. e.g. GRU, HMB"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Clinical Sex",
                "required": True,
                "data_type": "enum",
                "description": "https://www.hl7.org/fhir/patient.html#gender",
                "instructions": (
                    "Values from the FHIR"
                    " http://hl7.org/fhir/R4/valueset-administrative-gender.html"
                    " Value Set: Male, Female, Other"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["Male", "Female", "Other"],
            },
            {
                "key": None,
                "label": "Gender Identity",
                "required": False,
                "data_type": "string",
                "description": "TBD",
                "instructions": "Value set: TBD",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Race",
                "required": False,
                "data_type": "enum",
                "description": (
                    "As defined by the"
                    " http://hl7.org/fhir/us/core/StructureDefinition-us-core-patient-definitions.html#Patient.extension:race."
                ),
                "instructions": (
                    "If multiple race values are captured, it should go in the"
                    " Participant Observation and Conditions file. \n\nIf only"
                    " one values is captured it can be included in the single"
                    " attribute file for convenience. from the"
                    " https://hl7.org/fhir/us/core/CodeSystem-cdcrec.html."
                    " \n\nThis is an expansive code set that includes common"
                    " values used in US studies such as: White, American"
                    " Indian or Alaska Native, Black or African American,"
                    " Asian, Native Hawaiian or Other Pacific Islander."
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": [
                    "White",
                    "American Indian or Alaska Native",
                    "Black or African American",
                    "Asian",
                    "Native Hawaiian or Other Pacific Islander",
                ],
            },
            {
                "key": None,
                "label": "Ethnicity",
                "required": False,
                "data_type": "enum",
                "description": (
                    "As defined by the"
                    " http://hl7.org/fhir/us/core/StructureDefinition-us-core-patient-definitions.html#Patient.extension:ethnicity."
                ),
                "instructions": "Hispanic or Latino, Not Hispanic or Latino",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": [
                    "Hispanic or Latino",
                    "Not Hispanic or Latino",
                ],
            },
            {
                "key": None,
                "label": "Age at Study Enrollment Value",
                "required": False,
                "data_type": "number",
                "description": (
                    "Age participant was enrolled in the study given in the"
                    " units provided"
                ),
                "instructions": "Positive integer",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Study Enrollment Units",
                "required": False,
                "data_type": "string",
                "description": (
                    "Units for the age at study enrollment, days are the most"
                    " preferred, followed by months and then years. This"
                    " allows for different units to be used for children"
                    " versus adults. The maximum allowable age per HIPAA safe"
                    " habor is 90 years."
                ),
                "instructions": (
                    "One of values from the"
                    " https://www.hl7.org/fhir/valueset-age-units.html"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Affected Status",
                "required": True,
                "data_type": "boolean",
                "description": (
                    "If the participant is considered affected as part of the"
                    " study. This is provided as an example of an additional"
                    " field that is commonly used in genetic analysis."
                ),
                "instructions": None,
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Proband",
                "required": True,
                "data_type": "boolean",
                "description": (
                    "If known, whether the person identified by the"
                    " Participant ID is considered the proband of the family"
                ),
                "instructions": None,
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Species",
                "required": False,
                "data_type": "enum",
                "description": "The species of the research participant",
                "instructions": "Homo Sapiens, Canis lupus familiaris",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["Homo Sapiens", "Canis lupus familiaris"],
            },
            {
                "key": None,
                "label": "Last Known Vital Status",
                "required": False,
                "data_type": "enum",
                "description": (
                    "Vital status at last known participant contact"
                ),
                "instructions": (
                    "Alive, Deceased by Disease of Study, Deceased by Unknown"
                    " or Other Cause"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": [
                    "Alive",
                    "Deceased by Disease of Study",
                    "Deceased by Unknown or Other Cause",
                ],
            },
            {
                "key": None,
                "label": "Age at Status Value",
                "required": False,
                "data_type": "number",
                "description": (
                    "Time from birth to when the last known vital status was"
                    " collected. If the participant is deceased this should be"
                    " the same as the age at death. If the participant is"
                    " alive, this should be the age at last status check. If"
                    " the only contact with the participant is enrollment,"
                    " this should be equal to Age at Study Enrollment Value."
                    " The maximum allowable age per HIPAA safe harbor is 90"
                    " years."
                ),
                "instructions": "Positive integer",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Status Units",
                "required": False,
                "data_type": "enum",
                "description": (
                    "Units for the age, days are the most preferred, followed"
                    " by months and then years."
                ),
                "instructions": "Days, Months, Years if the age is known",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["Days", "Months", "Years"],
            },
        ],
    },
    {
        "template_name": "Participant Diseases",
        "template_description": (
            "Each row in this file captures a single disease observation event"
            " about one participant. The fields are mostly based off of the"
            ' Condition FHIR resource which defines condition as: "condition,'
            " problem, diagnosis, or other event, situation, issue, or"
            ' clinical concept that has risen to a level of concern". For most'
            " cohorts this will include the primary diseases, diagnoses, or"
            " problems that are under study. However, other conditions may be"
            " of interest such as pre-existing conditions, comorbidities,"
            " and/or recurrences depending on the study."
        ),
        "fields": [
            {
                "key": "PARTICIPANT|ID",
                "label": "Participant ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that is unique for each"
                    " participant."
                ),
                "instructions": (
                    "Participant ID that must exist in the Participant Details"
                    " File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Onset Value",
                "required": False,
                "data_type": "number",
                "description": "Age when the condition was known to start.",
                "instructions": "Positive integer",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Onset Units",
                "required": False,
                "data_type": "enum",
                "description": (
                    "Units for the age at recorded start, days are the most"
                    " preferred, followed by months and then years."
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["Days", "Months", "Years"],
            },
            {
                "key": None,
                "label": "Age at Abatement Value",
                "required": False,
                "data_type": "number",
                "description": "Age when the condition was known to end.",
                "instructions": "Positive integer",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Abatement Units",
                "required": False,
                "data_type": "enum",
                "description": (
                    "Units for the age at known abatement of the condition,"
                    " days are the most preferred, followed by months and then"
                    " years."
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["Days", "Months", "Years"],
            },
            {
                "key": None,
                "label": "Condition Name",
                "required": True,
                "data_type": "string",
                "description": (
                    "Only one per row. A name of the condition relevant for"
                    " the participant in the study. If not captured utilizing"
                    " a code set, please provide the original name utilized in"
                    " the study."
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Condition MONDO Code",
                "required": False,
                "data_type": "string",
                "description": (
                    "Only one per row. Ontology code for the condition"
                ),
                "instructions": (
                    "Any valid MONDO code from"
                    " https://www.ebi.ac.uk/ols/ontologies/mondo"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Verification Status",
                "required": False,
                "data_type": "enum",
                "description": (
                    "Whether this condition is confirmed (known positive) or"
                    " refuted (known negative)."
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["Positive", "Negative"],
            },
            {
                "key": None,
                "label": "Body Site Name",
                "required": False,
                "data_type": "string",
                "description": (
                    "Only one per row. Anatomical location of the condition"
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Body Site UBERON Code",
                "required": False,
                "data_type": "string",
                "description": (
                    "Only one per row. Ontology code describing the body site."
                ),
                "instructions": (
                    "Any Valid UBERON code from"
                    " https://www.ebi.ac.uk/ols/ontologies/uberon"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Category",
                "required": True,
                "data_type": "enum",
                "description": "Category of disease",
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["Cancer", "Structural Birth Defect"],
            },
        ],
    },
    {
        "template_name": "Participant Phenotypes",
        "template_description": (
            "Each row in this file captures a single phenotypic observation"
            " event about one participant. The fields are mostly based off of"
            " the Condition FHIR resource which defines condition as:"
            ' "condition, problem, diagnosis, or other event, situation,'
            " issue, or clinical concept that has risen to a level of"
            ' concern". The difference between this file and the Participant'
            " Diseases file is that the Condition Code must come from the"
            " Human Phenotype Ontology."
        ),
        "fields": [
            {
                "key": "PARTICIPANT|ID",
                "label": "Participant ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that is unique for each"
                    " participant."
                ),
                "instructions": (
                    "Participant ID that must exist in the Participant Details"
                    " File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Onset Value",
                "required": False,
                "data_type": "number",
                "description": "Age when the condition was known to start.",
                "instructions": "Positive integer",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Onset Units",
                "required": False,
                "data_type": "enum",
                "description": (
                    "Units for the age at recorded start, days are the most"
                    " preferred, followed by months and then years."
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["Days", "Months", "Years"],
            },
            {
                "key": None,
                "label": "Age at Abatement Value",
                "required": False,
                "data_type": "number",
                "description": "Age when the condition was known to end.",
                "instructions": "Positive integer",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Abatement Units",
                "required": False,
                "data_type": "enum",
                "description": (
                    "Units for the age at known abatement of the condition,"
                    " days are the most preferred, followed by months and then"
                    " years."
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["Days", "Months", "Years"],
            },
            {
                "key": None,
                "label": "Condition Name",
                "required": True,
                "data_type": "string",
                "description": (
                    "Only one per row. A name of the condition relevant for"
                    " the participant in the study. If not captured utilizing"
                    " a code set, please provide the original name utilized in"
                    " the study."
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Condition HPO Code",
                "required": False,
                "data_type": "string",
                "description": (
                    "Only one per row. Ontology code for the condition"
                ),
                "instructions": (
                    "Any valid HPO code from"
                    " https://www.ebi.ac.uk/ols/ontologies/hp"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Verification Status",
                "required": True,
                "data_type": "string",
                "description": (
                    "Whether this condition is confirmed (known positive) or"
                    " refuted (known negative)."
                ),
                "instructions": (
                    "Any value from"
                    " https://www.hl7.org/fhir/valueset-condition-ver-status.html"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Body Site Name",
                "required": False,
                "data_type": "string",
                "description": (
                    "Only one per row. Anatomical location of the condition"
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Body Site UBERON Code",
                "required": False,
                "data_type": "string",
                "description": (
                    "Only one per row. Ontology code describing the body site."
                ),
                "instructions": (
                    "Any Valid UBERON code from"
                    " https://www.ebi.ac.uk/ols/ontologies/uberon"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
        ],
    },
    {
        "template_name": "General Observations",
        "template_description": (
            "This file is a catch-all for any attributes about a participant"
            " that cannot adequately be captured in any of the other file"
            " types. The fields here are based on the FHIR Observation"
            ' resource which is defined as "simple name/value pair assertions'
            " with some metadata, but some observations group other"
            " observations together logically, or even are multi-component"
            ' observations". Observations can include vital signs, laboratory'
            " data, environment exposure, survey data and/or other clinical"
            " assessments. The DRC team can help advise on how best to"
            " represent your data as observations when needed."
        ),
        "fields": [
            {
                "key": "PARTICIPANT|ID",
                "label": "Participant ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that is unique for each"
                    " participant."
                ),
                "instructions": (
                    "Participant ID that must exist in the Participant Details"
                    " File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Observation Value",
                "required": False,
                "data_type": "number",
                "description": "Age when the observation was made.",
                "instructions": "Positive integer",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Observation Units",
                "required": False,
                "data_type": "string",
                "description": (
                    "Units for the age, days are the most preferred, followed"
                    " by months and then years."
                ),
                "instructions": (
                    "One of values from the"
                    " https://www.hl7.org/fhir/valueset-age-units.html"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Observation Name",
                "required": True,
                "data_type": "string",
                "description": (
                    "Only one per row. A name of the observation relevant for"
                    " the participant in the study. If not captured utilizing"
                    " a code set, please provide the original name utilized in"
                    " the study."
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Observation Ontology Ontobee URI",
                "required": False,
                "data_type": "string",
                "description": (
                    "Only one per row. Name of ontology for the observation"
                ),
                "instructions": "Ontology name from http://www.ontobee.org/",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Observation Code",
                "required": False,
                "data_type": "string",
                "description": (
                    "Only one per row. Ontology code for the observation."
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Category",
                "required": True,
                "data_type": "string",
                "description": (
                    "A code that classifies the general type of observation"
                    " being made."
                ),
                "instructions": (
                    "Any value from"
                    " https://www.hl7.org/fhir/valueset-observation-category.html#expansion"
                    " for observation categories."
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Interpretation",
                "required": False,
                "data_type": "string",
                "description": (
                    "A categorical assessment, providing a rough qualitative"
                    " interpretation of the observation value, such as"
                    " “normal” or “abnormal”."
                ),
                "instructions": (
                    "Any value from"
                    " https://www.hl7.org/fhir/valueset-observation-interpretation.html#expansion"
                    " for interpretations"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Status",
                "required": True,
                "data_type": "string",
                "description": (
                    "Whether this observation is confirmed (known positive) or"
                    " refuted (known negative)."
                ),
                "instructions": (
                    "Any value from"
                    " https://www.hl7.org/fhir/valueset-condition-ver-status.html"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Body Site Name",
                "required": False,
                "data_type": "string",
                "description": (
                    "Only one per row. Anatomical location of the condition"
                ),
                "instructions": "Free Text",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Body Site UBERON Code",
                "required": False,
                "data_type": "string",
                "description": (
                    "Only one per row. Ontology code describing the body site."
                ),
                "instructions": (
                    "Any Valid UBERON code from"
                    " https://www.ebi.ac.uk/ols/ontologies/uberon"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
        ],
    },
    {
        "template_name": "Family Trio",
        "template_description": (
            "Family information is required if there are any subjects that are"
            " related to each other. The most preferred way is providing"
            ' direct parent information, or the "Family Trio" template. This'
            " should be  used if there are IDs existing for the mother and"
            " father of the participant. If there is missing information about"
            " direct parents (e.g. it is only known that one participant is a"
            " grandparent), or if there is important information not captured"
            " by only using mother/father (e.g. twin relationships) the"
            ' "Complex Family" file type can be utilized.'
        ),
        "fields": [
            {
                "key": "PARTICIPANT|ID",
                "label": "Participant ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that is unique for each"
                    " participant."
                ),
                "instructions": (
                    "Participant ID that exists in the Participant Details"
                    " File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Mother Participant ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that describes the mother."
                ),
                "instructions": (
                    "Participant ID that exists in the Participant Details"
                    " File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Father Participant ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that describes the father."
                ),
                "instructions": (
                    "Participant ID that exists in the Participant Details"
                    " File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
        ],
    },
    {
        "template_name": "Complex Family",
        "template_description": (
            "Family information is required if there are any subjects that are"
            " related to each other. The most preferred way is providing"
            ' direct parent information, or the "Family Trio" template. This'
            " should be  used if there are IDs existing for the mother and"
            " father of the participant. If there is missing information about"
            " direct parents (e.g. it is only known that one participant is a"
            " grandparent), or if there is important information not captured"
            " by only using mother/father (e.g. twin relationships) the"
            ' "Complex Family" file type can be utilized.'
        ),
        "fields": [
            {
                "key": "PARTICIPANT|ID",
                "label": "Source Participant ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that describes this participant."
                ),
                "instructions": (
                    "Participant ID that must exist in the Participant Details"
                    " File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Target Participant ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Identifier of the participant that this participant is"
                    " the relative towards, must also be contained in this"
                    ' sheet. For example if "PF" is the father of "P1", the'
                    ' row should contains "PF" as the participant ID, "Father"'
                    ' as the value of Family Relationship and "P1" in this'
                    " field."
                ),
                "instructions": (
                    "Participant ID that must exist in the Participant Details"
                    " File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Family Relationship",
                "required": True,
                "data_type": "string",
                "description": (
                    "Use mother/father relationships to represent the family"
                    " relationships are preferred. Only utilize other"
                    " relationships as strictly necessary (e.g. parent"
                    " information is missing or to indicate twin"
                    " relationships)"
                ),
                "instructions": (
                    "http://hl7.org/fhir/R4/v3/FamilyMember/vs.html"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
        ],
    },
    {
        "template_name": "Biospecimen Collection Manifest",
        "template_description": (
            "This file is expected to be supplied by the research PI and"
            " contains the most common and critical information about the"
            " collection of the specimen such as its basic biological"
            " characteristics (e.g. composition, anatomical site), consenting"
            " information, and (if applicable) specimen grouping information"
            " (not to be confused with aliquots)."
        ),
        "fields": [
            {
                "key": "PARTICIPANT|ID",
                "label": "Participant ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that is unique for each"
                    " participant."
                ),
                "instructions": (
                    "Participant ID that must exist in the Participant Details"
                    " File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": "BIOSPECIMEN_GROUP|ID",
                "label": "Specimen ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "If multiple aliquots have been sent from the same sample"
                    " (e.g. for WGS and RNA-Seq characterization) a"
                    " deidentified Specimen ID that links them together"
                ),
                "instructions": "A unique string per sample within the study",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Consent Short Name",
                "required": False,
                "data_type": "string",
                "description": "Consent type",
                "instructions": "Short name of the consent group code",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Consent Group",
                "required": False,
                "data_type": "string",
                "description": (
                    "Indicate which data use limitation, as indicated on the"
                    " provided Institutional Certification, is associated with"
                    " each participant. The dbGaP style consent code"
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Tissue Type Name",
                "required": False,
                "data_type": "string",
                "description": (
                    "Text term that represents a description of the kind of"
                    " tissue collected with respect to disease status or"
                    " proximity to tumor tissue."
                ),
                "instructions": (
                    "Examples: Tumor, Normal, Abnormal, Peritumoral"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Tissue Type NCIt Code",
                "required": False,
                "data_type": "string",
                "description": (
                    "Any valid code from NCIt ontology. Only one code per row"
                ),
                "instructions": (
                    "Any Valid NCIt code from"
                    " https://www.ebi.ac.uk/ols/ontologies/ncit"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Composition Name",
                "required": True,
                "data_type": "string",
                "description": (
                    "Text term that represents the cellular composition of the"
                    " sample"
                ),
                "instructions": (
                    "Examples: Saliva, Buccal Cells, Blood, Solid Tissue,"
                    " Derived Cell Lines, DNA, RNA, Other"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Composition SNOMED CT Code",
                "required": False,
                "data_type": "string",
                "description": (
                    "Any valid code from SNOMED CT ontology. Only one code"
                    " per row"
                ),
                "instructions": (
                    "Any Valid SNOMEDCT code from"
                    " https://bioportal.bioontology.org/ontologies/SNOMEDCT"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Body Site Name",
                "required": True,
                "data_type": "string",
                "description": (
                    "The anatomical location from which the sample was"
                    " procured. If blood, draw location is known or other"
                    " method of blood acquisition. In the case of tissue"
                    " biopsy samples, note the location of the biopsy."
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Body Site UBERON Code",
                "required": False,
                "data_type": "string",
                "description": (
                    "Only one code per row. Any valid code from UBERON"
                    " ontology"
                ),
                "instructions": (
                    "Any Valid UBERON code from"
                    " https://www.ebi.ac.uk/ols/ontologies/uberon"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Collection Value",
                "required": False,
                "data_type": "number",
                "description": (
                    "Age at the time biospecimen was acquired, expressed in"
                    " time since birth"
                ),
                "instructions": "Positive integer",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Age at Collection Units",
                "required": False,
                "data_type": "string",
                "description": (
                    "Units for the age, days are the most preferred, followed"
                    " by months and then years."
                ),
                "instructions": (
                    "One of values from the"
                    " https://www.hl7.org/fhir/valueset-age-units.html"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Method of Sample Procurement",
                "required": False,
                "data_type": "string",
                "description": (
                    "The method used to procure the sample used to extract"
                    " analyte(s)"
                ),
                "instructions": (
                    "Examples: Autopsy, Biopsy, Subtotal Resections,\nGross"
                    " Total Resections, Blood Draw,\nBone Marrow Aspiration,"
                    " \nSurgical Resections"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Ischemic Time",
                "required": False,
                "data_type": "number",
                "description": (
                    "Total Ischemic time for a sample. Interval between actual"
                    " death, presumed death, or cross clamp application and"
                    " final tissue stabilization"
                ),
                "instructions": "Positive integer",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Ischemic Units",
                "required": False,
                "data_type": "enum",
                "description": "Units of ischemic time",
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["Minutes"],
            },
            {
                "key": None,
                "label": "Origin Specimen ID",
                "required": False,
                "data_type": "string",
                "description": (
                    "The original specimen from which this specimen was"
                    " derived. Helps track where derived cell line specimens"
                    " came from"
                ),
                "instructions": (
                    "A specimen ID that must exist in the Biospecimen"
                    " Collection Manifest"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Specimen Group ID",
                "required": False,
                "data_type": "string",
                "description": (
                    "Identifies a group of specimens that were collected at"
                    " the same time"
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
        ],
    },
    {
        "template_name": "Biobank Manifest",
        "template_description": (
            "This file is expected to be supplied by the research PI and"
            " contains the most common and critical information about the"
            " collection of the specimen such as its basic biological"
            " characteristics (e.g. composition, anatomical site), consenting"
            " information, and (if applicable) specimen grouping information"
            " (not to be confused with aliquots)."
        ),
        "fields": [
            {
                "key": "BIOSPECIMEN_GROUP|ID",
                "label": "Specimen ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "If multiple aliquots have been sent from the same sample"
                    " (e.g. for WGS and RNA-Seq characterization) a"
                    " deidentified Specimen ID that links them together"
                ),
                "instructions": (
                    "Specimen ID that must exist in the Biospecimen Collectin"
                    " Manifest File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": "BIOSPECIMEN|ID",
                "label": "Aliquot ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that exactly matches the"
                    " identifier provided to the sequencing center. These"
                    " identifiers being the same are critical to linking the"
                    " genomic and clinical data and having data approved for"
                    " release. Some participants or samples may have multiple"
                    " aliquots and as such should have a seperate entry per"
                    " aliquot sent to the sequencing center. The Aliquot ID"
                    " could be identical to a Specimen ID in the case where"
                    " there is only one aliquot per individual being sent to"
                    " the sequencing center"
                ),
                "instructions": (
                    "A unique string per aliquot within the study."
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Analyte Type",
                "required": True,
                "data_type": "enum",
                "description": (
                    "Text term that represents the kind of molecular specimen"
                    " analyte"
                ),
                "instructions": "DNA, RNA, Other",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["DNA", "RNA", "Other"],
            },
            {
                "key": None,
                "label": "Quantity Value",
                "required": False,
                "data_type": "number",
                "description": "Quantity of the specimen availlalble",
                "instructions": "Float",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Quantity Units",
                "required": False,
                "data_type": "enum",
                "description": "The units for the quantity",
                "instructions": "ul (microliters)",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["ul"],
            },
            {
                "key": None,
                "label": "Concentration Value",
                "required": False,
                "data_type": "number",
                "description": "Concentration of the specimen quantity",
                "instructions": "Float",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Concentration Units",
                "required": False,
                "data_type": "enum",
                "description": "Units of the concentration value",
                "instructions": "mg/ml (milligrams per milliliter)",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["mg/ml"],
            },
            {
                "key": None,
                "label": "Preservation Method",
                "required": False,
                "data_type": "string",
                "description": "TBD",
                "instructions": "e.g. FFE",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Availability Status",
                "required": False,
                "data_type": "string",
                "description": "TBD",
                "instructions": "e.g. onsite, shipped, sequenced, depleted",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
        ],
    },
    {
        "template_name": "Aliquot Manifest",
        "template_description": (
            "The fields in this file may seem like they could/should be part"
            " of one of the other specimen templates. The reason why this"
            " information is in its own template is because sometimes it is"
            " produced by the research PI and other times it is produced by"
            " the sequencing center. \n\nIn the former case, the research PI"
            " (or an associated lab) has taken ownership over portioning the"
            " specimens into aliquots and creating the inventory of specimens,"
            " aliquots, and analyte types before they are sent for sequencing."
            " In the latter case, the sequencing center may spin out the"
            " analyte types to create the aliquots, in which case it becomes"
            " the single source of truth for specimens and aliquots."
        ),
        "fields": [
            {
                "key": "BIOSPECIMEN_GROUP|ID",
                "label": "Specimen ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "If multiple aliquots have been sent from the same sample"
                    " (e.g. for WGS and RNA-Seq characterization) a"
                    " deidentified Specimen ID that links them together"
                ),
                "instructions": (
                    "Specimen ID that must exist in the Biospecimen Collectin"
                    " Manifest File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": "BIOSPECIMEN|ID",
                "label": "Aliquot ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that exactly matches the"
                    " identifier provided to the sequencing center. These"
                    " identifiers being the same are critical to linking the"
                    " genomic and clinical data and having data approved for"
                    " release. Some participants or samples may have multiple"
                    " aliquots and as such should have a seperate entry per"
                    " aliquot sent to the sequencing center. The Aliquot ID"
                    " could be identical to a Specimen ID in the case where"
                    " there is only one aliquot per individual being sent to"
                    " the sequencing center"
                ),
                "instructions": (
                    "Aliquot ID that must exist in the Biobank Manifest File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Analyte Type",
                "required": True,
                "data_type": "enum",
                "description": (
                    "Text term that represents the kind of molecular specimen"
                    " analyte"
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["DNA", "RNA", "Other"],
            },
            {
                "key": None,
                "label": "Sequencing Center",
                "required": True,
                "data_type": "string",
                "description": (
                    "The institution that sequenced the participant's aliquot"
                ),
                "instructions": None,
                "missing_values": None,
                "accepted_values": None,
            },
        ],
    },
    {
        "template_name": "Sequencing File Manifest",
        "template_description": (
            "This file captures the details of the sequencing experiment"
            " performed by the sequencing center for all of the aliquots in"
            " the study. We expect to receive this file from the sequencing"
            " center. \n\nEach row captures the experiment parameters or"
            " inputs to the sequencing run (e.g. strategy, library prep kit,"
            " etc), the aliquot ID for which the experiment was performed, and"
            " the sequencing file that was output from the experiment. Some"
            " rows may have repetitive information (e.g. experiment details)"
            " since each experiment may produce multiple sequencing files per"
            " aliquot."
        ),
        "fields": [
            {
                "key": "BIOSPECIMEN|ID",
                "label": "Aliquot ID",
                "required": True,
                "data_type": "string",
                "description": (
                    "Deidentified identifier that exactly matches the"
                    " identifier provided to the sequencing center. These"
                    " identifiers being the same are critical to linking the"
                    " genomic and clinical data and having data approved for"
                    " release. Some participants or samples may have multiple"
                    " aliquots and as such should have a seperate entry per"
                    " aliquot sent to the sequencing center. The Aliquot ID"
                    " could be identical to a Specimen ID in the case where"
                    " there is only one aliquot per individual being sent to"
                    " the sequencing center"
                ),
                "instructions": (
                    "Aliquot ID that must exist in the Aliquot Manifest File"
                ),
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Sequencing Center",
                "required": True,
                "data_type": "string",
                "description": (
                    "The institution that sequenced the participant's aliquot"
                ),
                "instructions": "Free Text",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": "SEQUENCING|ID",
                "label": "Sequencing Output Filepath",
                "required": True,
                "data_type": "string",
                "description": (
                    "The path to the sequencing file generated by the"
                    " sequencing center"
                ),
                "instructions": "One path per row",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Sequencing Output File Hash",
                "required": False,
                "data_type": "string",
                "description": (
                    "Hash of the file content used to validate successful file"
                    " transfer"
                ),
                "instructions": (
                    "Any valid hash value for the accepted hashing algorithms"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "File Hash Algorithm",
                "required": False,
                "data_type": "enum",
                "description": (
                    "The identifier of the hashing algorithm used to hash the"
                    " sequencing output file"
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["MD5", "SHA1", "SHA256", "SHA512"],
            },
            {
                "key": None,
                "label": "Reference Genome",
                "required": True,
                "data_type": "enum",
                "description": (
                    "Original reference genome of the sequencing files"
                    " produced by the sequencing center"
                ),
                "instructions": (
                    "Hudson Alpha Files: GRCh38 or hg19\nBroad Files: GRCh38"
                    " (Get enum from Bix)"
                ),
                "missing_values": None,
                "accepted_values": ["GRCh38", "hg19"],
            },
            {
                "key": None,
                "label": "Experiment Strategy",
                "required": True,
                "data_type": "enum",
                "description": "Library strategy",
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": [
                    "WGS",
                    "WXS",
                    "RNA-Seq",
                    "miRNA-Seq",
                    "Linked-Read WGS (10x Chromium)",
                ],
            },
            {
                "key": None,
                "label": "Experiment Date",
                "required": False,
                "data_type": "date",
                "description": "Experiment date",
                "instructions": "Valid RFC3339 date string",
                "missing_values": None,
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Sequencing Library Name",
                "required": True,
                "data_type": "string",
                "description": "Name of sequencing library",
                "instructions": (
                    "Unique identifier for the sequencing run within the study"
                ),
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Instrument Model",
                "required": False,
                "data_type": "string",
                "description": "Specific model of sequencing instrument used",
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Sequencing Platform",
                "required": True,
                "data_type": "enum",
                "description": (
                    "Name of the platform used to do the sequencing"
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": [
                    "Illumina",
                    "SOLiD",
                    "LS454",
                    "Ion Torrent",
                    "Complete Genomics",
                    "PacBio",
                    "(Jo Lynne has additional platforms to add)",
                ],
            },
            {
                "key": None,
                "label": "Library Strand",
                "required": False,
                "data_type": "enum",
                "description": "Library stranded-ness",
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": [
                    "Unstranded",
                    "First Stranded",
                    "Second Stranded",
                ],
            },
            {
                "key": None,
                "label": "Library Selection",
                "required": False,
                "data_type": "enum",
                "description": "Library selection method",
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": [
                    "Hybrid Selection",
                    "PCR",
                    "Affinity Enrichment",
                    "Poly-T Enrichment",
                    "Random",
                    "rRNA Depletion",
                    "miRNA Size Fractionation",
                ],
            },
            {
                "key": None,
                "label": "Library Prep Kit",
                "required": False,
                "data_type": "string",
                "description": (
                    "Name of library preparation kit. Used to capture the"
                    " fragments in a library"
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Library BED File Download Link",
                "required": False,
                "data_type": "string",
                "description": (
                    "Link to download the library BED files for the prep kit"
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Is Paired End",
                "required": True,
                "data_type": "enum",
                "description": (
                    "Specifies whether reads have paired end or not"
                ),
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": ["0", "1", "2"],
            },
            {
                "key": None,
                "label": "Expected Mean Insert Size",
                "required": False,
                "data_type": "string",
                "description": (
                    "One paired-end read is referred to a pair of short reads"
                    " sequenced from two ends of one long sequence fragment"
                    " and the sequence fragment length (the distance between"
                    " paired-end reads) is the insert size"
                ),
                "instructions": "Positive Integer",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Expected Mean Depth",
                "required": False,
                "data_type": "string",
                "description": (
                    "Average number of times that a given nucleotide in the"
                    " genome has been read in an experiment"
                ),
                "instructions": "Positive Integer",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Expected Mean Read Length",
                "required": False,
                "data_type": "string",
                "description": (
                    "Average number of base pairs sequenced from a DNA"
                    " fragment"
                ),
                "instructions": "Positive Integer",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Expected Total Reads",
                "required": False,
                "data_type": "string",
                "description": (
                    "Inferred sequence of base pairs (or base pair"
                    " probabilities) corresponding to all or part of a single"
                    " DNA fragment"
                ),
                "instructions": "Positive Integer",
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Quality Score System",
                "required": False,
                "data_type": "string",
                "description": "Yuankun will determine whether this is needed",
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
            {
                "key": None,
                "label": "Quality Score Value",
                "required": False,
                "data_type": "string",
                "description": "Yuankun will determine whether this is needed",
                "instructions": None,
                "missing_values": ["Not Able to Provide"],
                "accepted_values": None,
            },
        ],
    },
]
