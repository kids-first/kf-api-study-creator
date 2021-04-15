# 📓 Data Validation Report for `SD_MEW0YEB0`

## 📂 Files Validated

<br>

**/data/sd_mew0yeb0/validation/**

| Files                   |
| :---------------------- |
| clinical\.csv           |
| participant_sample\.csv |

## #️⃣ Counts

<details markdown="1">
<summary><b>Click to expand table</b></summary>

| Entity                               | Count |
| :----------------------------------- | ----: |
| FAMILY\.ID                           |     2 |
| PARTICIPANT\.ID                      |     2 |
| GENOMIC_FILE\.URL_LIST               |     1 |
| SEQUENCING\.PLATFORM                 |     0 |
| SEQUENCING\.PAIRED_END               |     0 |
| SEQUENCING\.STRATEGY                 |     0 |
| SEQUENCING\.LIBRARY_NAME             |     0 |
| GENOMIC_FILE\.REFERENCE_GENOME       |     0 |
| GENOMIC_FILE\.HARMONIZED             |     0 |
| SEQUENCING\.ID                       |     0 |
| BIOSPECIMEN\.SAMPLE_PROCUREMENT      |     0 |
| BIOSPECIMEN\.VOLUME_UL               |     0 |
| BIOSPECIMEN\.CONCENTRATION_MG_PER_ML |     0 |
| BIOSPECIMEN\.SHIPMENT_DATE           |     0 |
| BIOSPECIMEN\.SHIPMENT_ORIGIN         |     0 |
| BIOSPECIMEN\.SPATIAL_DESCRIPTOR      |     0 |
| BIOSPECIMEN\.EVENT_AGE_DAYS          |     0 |
| BIOSPECIMEN\.TUMOR_DESCRIPTOR        |     0 |
| BIOSPECIMEN\.ANATOMY_SITE            |     0 |
| BIOSPECIMEN\.TISSUE_TYPE             |     0 |
| BIOSPECIMEN\.COMPOSITION             |     0 |
| BIOSPECIMEN\.ANALYTE                 |     0 |
| GENOMIC_FILE\.ID                     |     0 |
| PARTICIPANT\.ENROLLMENT_AGE_DAYS     |     0 |
| PARTICIPANT\.SPECIES                 |     0 |
| PARTICIPANT\.RACE                    |     0 |
| PARTICIPANT\.ETHNICITY               |     0 |
| PARTICIPANT\.GENDER                  |     0 |
| BIOSPECIMEN\.ID                      |     0 |
| SEQUENCING\.INSTRUMENT               |     0 |

</details>

## 🚦 Relationship Tests

### Result Summary

| Result             | # of Tests |
| :----------------- | ---------: |
| **❌ Fail**        |          2 |
| **✅ Success**     |          6 |
| **🔘 Did Not Run** |         49 |

#### ❌ Each PARTICIPANT\.ID links to at least 1 BIOSPECIMEN\.ID

| Errors                                                                 |
| :--------------------------------------------------------------------- |
| All 2 `PARTICIPANT` in the dataset are linked to 0 `BIOSPECIMEN.ID` |

| Locations               |
| :---------------------- |
| participant_sample\.csv |

#### ❌ Each GENOMIC_FILE\.URL_LIST links to exactly 1 GENOMIC_FILE\.ID

| Errors                                                                         |
| :----------------------------------------------------------------------------- |
| All 1 `GENOMIC_FILE.URL_LIST` in the dataset are linked to 0 `GENOMIC_FILE.ID` |

| Locations     |
| :------------ |
| clinical\.csv |

#### ✅ Each FAMILY\.ID links to at least 1 PARTICIPANT\.ID

#### ✅ Each PARTICIPANT\.ID links to at most 1 PARTICIPANT\.GENDER

#### ✅ Each PARTICIPANT\.ID links to at most 1 PARTICIPANT\.ETHNICITY

#### ✅ Each PARTICIPANT\.ID links to at most 1 PARTICIPANT\.RACE

#### ✅ Each PARTICIPANT\.ID links to at most 1 PARTICIPANT\.SPECIES

#### ✅ Each PARTICIPANT\.ID links to at most 1 PARTICIPANT\.ENROLLMENT_AGE_DAYS

🔘 Each BIOSPECIMEN\.ID links to exactly 1 PARTICIPANT\.ID

🔘 Each GENOMIC_FILE\.ID links to exactly 1 SEQUENCING\.ID

🔘 Each SEQUENCING\.ID links to at least 1 GENOMIC_FILE\.ID

🔘 Each GENOMIC_FILE\.ID links to exactly 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at least 1 GENOMIC_FILE\.ID

🔘 Each PARTICIPANT\.GENDER links to at least 1 PARTICIPANT\.ID

🔘 Each PARTICIPANT\.ETHNICITY links to at least 1 PARTICIPANT\.ID

🔘 Each PARTICIPANT\.RACE links to at least 1 PARTICIPANT\.ID

🔘 Each PARTICIPANT\.SPECIES links to at least 1 PARTICIPANT\.ID

🔘 Each PARTICIPANT\.ENROLLMENT_AGE_DAYS links to at least 1 PARTICIPANT\.ID

🔘 Each BIOSPECIMEN\.ANALYTE links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to exactly 1 BIOSPECIMEN\.ANALYTE

🔘 Each BIOSPECIMEN\.COMPOSITION links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at most 1 BIOSPECIMEN\.COMPOSITION

🔘 Each BIOSPECIMEN\.TISSUE_TYPE links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at most 1 BIOSPECIMEN\.TISSUE_TYPE

🔘 Each BIOSPECIMEN\.ANATOMY_SITE links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at most 1 BIOSPECIMEN\.ANATOMY_SITE

🔘 Each BIOSPECIMEN\.TUMOR_DESCRIPTOR links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at most 1 BIOSPECIMEN\.TUMOR_DESCRIPTOR

🔘 Each BIOSPECIMEN\.EVENT_AGE_DAYS links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at most 1 BIOSPECIMEN\.EVENT_AGE_DAYS

🔘 Each BIOSPECIMEN\.SPATIAL_DESCRIPTOR links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at most 1 BIOSPECIMEN\.SPATIAL_DESCRIPTOR

🔘 Each BIOSPECIMEN\.SHIPMENT_ORIGIN links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at most 1 BIOSPECIMEN\.SHIPMENT_ORIGIN

🔘 Each BIOSPECIMEN\.SHIPMENT_DATE links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at most 1 BIOSPECIMEN\.SHIPMENT_DATE

🔘 Each BIOSPECIMEN\.CONCENTRATION_MG_PER_ML links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at most 1 BIOSPECIMEN\.CONCENTRATION_MG_PER_ML

🔘 Each BIOSPECIMEN\.VOLUME_UL links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at most 1 BIOSPECIMEN\.VOLUME_UL

🔘 Each BIOSPECIMEN\.SAMPLE_PROCUREMENT links to at least 1 BIOSPECIMEN\.ID

🔘 Each BIOSPECIMEN\.ID links to at most 1 BIOSPECIMEN\.SAMPLE_PROCUREMENT

🔘 Each GENOMIC_FILE\.HARMONIZED links to at least 1 GENOMIC_FILE\.ID

🔘 Each GENOMIC_FILE\.ID links to exactly 1 GENOMIC_FILE\.HARMONIZED

🔘 Each GENOMIC_FILE\.REFERENCE_GENOME links to at least 1 GENOMIC_FILE\.ID

🔘 Each GENOMIC_FILE\.ID links to exactly 1 GENOMIC_FILE\.REFERENCE_GENOME

🔘 Each GENOMIC_FILE\.ID links to exactly 1 GENOMIC_FILE\.URL_LIST

🔘 Each SEQUENCING\.LIBRARY_NAME links to exactly 1 SEQUENCING\.ID

🔘 Each SEQUENCING\.ID links to at most 1 SEQUENCING\.LIBRARY_NAME

🔘 Each SEQUENCING\.STRATEGY links to at least 1 SEQUENCING\.ID

🔘 Each SEQUENCING\.ID links to exactly 1 SEQUENCING\.STRATEGY

🔘 Each SEQUENCING\.PAIRED_END links to at least 1 SEQUENCING\.ID

🔘 Each SEQUENCING\.ID links to exactly 1 SEQUENCING\.PAIRED_END

🔘 Each SEQUENCING\.PLATFORM links to at least 1 SEQUENCING\.ID

🔘 Each SEQUENCING\.ID links to at most 1 SEQUENCING\.PLATFORM

🔘 Each SEQUENCING\.INSTRUMENT links to at least 1 SEQUENCING\.ID

🔘 Each SEQUENCING\.ID links to at most 1 SEQUENCING\.INSTRUMENT

## 🚦 Gap Tests

### Result Summary

| Result             | # of Tests |
| :----------------- | ---------: |
| **❌ Fail**        |          1 |
| **✅ Success**     |          0 |
| **🔘 Did Not Run** |          0 |

#### ❌ All resolved links are hierarchically direct

| Errors                                                                                           |
| :----------------------------------------------------------------------------------------------- |
| `GENOMIC_FILE.URL_LIST.['s3://haeg38ak_P1.bam']` is linked to \['`PARTICIPANT.ID.P2`', '`PARTICIPANT.ID.P1`'\] |

| Locations               | Values                                                       |
| :---------------------- | :----------------------------------------------------------- |
| clinical\.csv           | This file contains all errors in the **Errors** table above. |
| participant_sample\.csv | `PARTICIPANT.ID.P1`,`PARTICIPANT.ID.P2`                          |

## 🚦 Attribute Value Tests

### Result Summary

| Result             | # of Tests |
| :----------------- | ---------: |
| **❌ Fail**        |          0 |
| **✅ Success**     |          0 |
| **🔘 Did Not Run** |         47 |

🔘 PARTICIPANT\.RACE must be one of \[`"American Indian or Alaska Native"`, `"Asian"`, `"Black or African American"`, `"More Than One Race"`, `"Native Hawaiian or Other Pacific Islander"`, `"Other"`, `"White"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 PARTICIPANT\.ENROLLMENT_AGE_DAYS must be a number x such that 0 <= x <= 32872\.

🔘 PARTICIPANT\.ENROLLMENT_AGE\.VALUE must be a number > 0\.

🔘 PARTICIPANT\.ENROLLMENT_AGE\.UNITS must be one of \[`"Days"`, `"Months"`, `"Years"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 PARTICIPANT\.ETHNICITY must be one of \[`"Hispanic or Latino"`, `"Not Hispanic or Latino"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 PARTICIPANT\.GENDER must be one of \[`"Female"`, `"Male"`, `"Other"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 PARTICIPANT\.SPECIES must be one of \[`"Canis lupus familiaris"`, `"Homo Sapiens"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 PARTICIPANT\.CONSENT_TYPE must be one of \[`"DS-CHD"`, `"DS-CHD-IRB"`, `"DS-OBD-MDS"`, `"DS-OBDR-MDS"`, `"DS-OC-PUB-MDS"`, `"GRU"`, `"HMB-IRB"`, `"HMB-MDS"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 PARTICIPANT\.LAST_CONTACT_AGE_DAYS must be a number x such that 0 <= x <= 32872\.

🔘 PARTICIPANT\.LAST_CONTACT_AGE\.VALUE must be a number > 0\.

🔘 PARTICIPANT\.LAST_CONTACT_AGE\.UNITS must be one of \[`"Days"`, `"Months"`, `"Years"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 BIOSPECIMEN\.EVENT_AGE_DAYS must be a number x such that 0 <= x <= 32872\.

🔘 BIOSPECIMEN\.EVENT_AGE\.VALUE must be a number > 0\.

🔘 BIOSPECIMEN\.EVENT_AGE\.UNITS must be one of \[`"Days"`, `"Months"`, `"Years"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 BIOSPECIMEN\.ANALYTE must be one of \[`"DNA"`, `"Other"`, `"RNA"`, `"Virtual"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 BIOSPECIMEN\.CONCENTRATION_MG_PER_ML must be a number > 0\.

🔘 BIOSPECIMEN\.SAMPLE_PROCUREMENT must be one of \[`"Autopsy"`, `"Biopsy"`, `"Blood Draw"`, `"Gross Total Resection"`, `"Other"`, `"Subtotal Resection"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 BIOSPECIMEN\.SHIPMENT_DATE must be a valid representation of a Date or Datetime object\.

🔘 BIOSPECIMEN\.VOLUME_UL must be a number > 0\.

🔘 DIAGNOSIS\.EVENT_AGE_DAYS must be a number > 0\.

🔘 DIAGNOSIS\.CATEGORY must be one of \[`"Cancer"`, `"Other"`, `"Structural Birth Defect"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 GENOMIC_FILE\.AVAILABILITY must be one of \[`"Cold Storage"`, `"Immediate Download"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 GENOMIC_FILE\.DATA_TYPE must be one of \[`"Aligned Reads"`, `"Aligned Reads Index"`, `"Expression"`, `"Gene Expression"`, `"Gene Fusions"`, `"Histology Images"`, `"Isoform Expression"`, `"Operation Reports"`, `"Other"`, `"Pathology Reports"`, `"Radiology Images"`, `"Radiology Reports"`, `"Simple Nucleotide Variations"`, `"Somatic Copy Number Variations"`, `"Somatic Structural Variations"`, `"Unaligned Reads"`, `"Variant Calls"`, `"Variant Calls Index"`, `"gVCF"`, `"gVCF Index"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 GENOMIC_FILE\.SIZE must be a number >= 0\.

🔘 OUTCOME\.EVENT_AGE_DAYS must be a number x such that 0 <= x <= 32872\.

🔘 OUTCOME\.EVENT_AGE\.VALUE must be a number > 0\.

🔘 OUTCOME\.EVENT_AGE\.UNITS must be one of \[`"Days"`, `"Months"`, `"Years"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 OUTCOME\.DISEASE_RELATED must be one of \[`"No"`, `"Yes"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 OUTCOME\.VITAL_STATUS must be one of \[`"Alive"`, `"Deceased"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 PHENOTYPE\.EVENT_AGE_DAYS must be a number x such that 0 <= x <= 32872\.

🔘 PHENOTYPE\.EVENT_AGE\.VALUE must be a number > 0\.

🔘 PHENOTYPE\.EVENT_AGE\.UNITS must be one of \[`"Days"`, `"Months"`, `"Years"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 PHENOTYPE\.OBSERVED must be one of \[`"Negative"`, `"Positive"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 READ_GROUP\.PAIRED_END must be one of \[`"1"`, `"2"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 READ_GROUP\.LANE_NUMBER must be a number > 0\.

🔘 READ_GROUP\.QUALITY_SCALE must be one of \[`"Illumina13"`, `"Illumina15"`, `"Illumina18"`, `"Sanger"`, `"Solexa"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 SEQUENCING\.DATE must be a valid representation of a Date or Datetime object\.

🔘 SEQUENCING\.STRATEGY must be one of \[`"Linked-Read WGS (10x Chromium)"`, `"Other"`, `"RNA-Seq"`, `"Targeted Sequencing"`, `"WGS"`, `"WXS"`, `"miRNA-Seq"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 SEQUENCING\.LIBRARY_STRAND must be one of \[`"First Stranded"`, `"Other"`, `"Second Stranded"`, `"Unstranded"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 SEQUENCING\.MAX_INSERT_SIZE must be a number > 0\.

🔘 SEQUENCING\.MEAN_DEPTH must be a number > 0\.

🔘 SEQUENCING\.MEAN_INSERT_SIZE must be a number > 0\.

🔘 SEQUENCING\.MEAN_READ_LENGTH must be a number > 0\.

🔘 SEQUENCING\.PAIRED_END must be one of \[`"False"`, `"True"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 SEQUENCING\.PLATFORM must be one of \[`"Complete Genomics"`, `"Illumina"`, `"Ion Torrent"`, `"LS454"`, `"Other"`, `"PacBio"`, `"SOLiD"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

🔘 SEQUENCING\.TOTAL_READS must be a number > 0\.

🔘 STUDY_FILE\.AVAILABILITY must be one of \[`"Cold Storage"`, `"Immediate Download"`\] or \[`""`, `"Not Allowed To Collect"`, `"Not Applicable"`, `"Not Available"`, `"Not Reported"`, `"Reported Unknown"`\]

## 🚦 Count Tests

### Result Summary

| Result             | # of Tests |
| :----------------- | ---------: |
| **❌ Fail**        |          0 |
| **✅ Success**     |          0 |
| **🔘 Did Not Run** |          0 |
