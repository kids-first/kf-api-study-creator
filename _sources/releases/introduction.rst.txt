Introduction
============

Publishing new data to the research community is an important role of the
Data Resource Center.
The Data Resource Center does this through *releasing* finalized data for one
or more new or existing studies.
A *release* will first be invoked then *staged* for publication whence it will
be reviewed and *published*.
Once a release has been published, the new data will be available to end users.

The Study Creator helps the Data Resource Center perform releases by tracking
and automating some steps in the process and by doing so aims to:
- Ensure consistency of the release process
- Reduce liklihood of publishing faulty data
- Create an auditable history of past data changes and publications

Service Coordination
--------------------

There are several services which deliver and act on data in Kids First.
Many of these services rely on internal operations to process new data and
prepare it for distribution to the end users.
The Data Resource Center has formalized steps in its release process to notify,
using a standard specification, downstream services.
Any service that is deemed critical to the distribution of new data is expected
to accept these notifications and respond with the current status of processing
the data.
In this way, the Data Resource Center may ensure that all necessary services
have correctly processed the new data before publishing it for general
consumption.

Versioning
----------

The Data Resource Center includes version numbers with each release it makes
to assist in auditing.
Release version numbers follow semantic versioning with major releases
signifying data changes that impact all studies (such as moving or addition
of data fields).
Minor versions encompass any changes or additions to one or more studies.
Patch versions are reserved for releases being staged or unpublished, including
failed releases.
A release will begin its life as an incremental patch but will be updated to
bump the major or minor version and reset the patch number upon being
published.
