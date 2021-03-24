# C2M2 Submission Generator

This application contains a generator to transform Kids First data into
a submission directory to be submitted to CFDE.

## Running

Install the application as usual makng sure to also install development
requirements:
```
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

The command to generate a submission directory may be run as such:
```
DATASERVICE_URL=https://kf-api-dataservice.kidsfirstdrc.org ./manage.py c2m2_load
```

The script will create a new directory (`c2m2_submission` by default) that
will hold all of the C2M2 formatted files.
This directory may then be submitted by using the `cfde-submit` tool:
```
cfde-submit  run c2m2_submission
```
