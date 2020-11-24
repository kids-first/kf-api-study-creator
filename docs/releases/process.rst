Release Process
===============

In order to standardize processing across services, the Data Resource Center
has defined the key steps in the release process.

1) Initialization
2) Processing
3) Staging and Review
4) Publication
5) Completion

Step 1: Initialization
----------------------

During this step, the Data Resource Center notifies all required services of a
new release and the included studies.
If any of the services do not accept the new release or are unhealthy in some
other way, the release will not be allowed to continue and will be cancelled
immediately.
When all required services respond positively, the next step will commence.
The Data Resource Center will also assign a tentative version id by
incrementing the patch number of the last created release's version
(regardless of its publication status).

Step 2: Processing
------------------

After successfully verifying all required services are ready to accept the
new release, the Data Resource Center sends a notification to all required
services instructing them to begin the processing step.
During this step, the services retrieve the latest data and manipulate it as
necessary for distribution.
Once each service has completed its work, it well report back to the Data
Resource Center that it is done and wait for further instruction.

Step 3: Review
--------------

When all required services have completed the processing step and reported
back successfully, the release will be said to be staged.
During this time, the Data Resource Center may review the results of the
processing for quality and may hold the release if necessary.

Step 4: Publication
-------------------

Once the Data Resource Center has declared the release ready for publication,
a member of the Data Resource Center wil publish the release.
Doing so will send notifications to all the required services telling them to
make public the data which they produced in the processing step.
The Data Resource Center will update the version of this release by
incrementing either the major or minor version depending on the classification
of the release.
During this step, required services should do minimal work needed to make the
data public so as to publish as quickly as possible.
All of the intense work should have been completed up front during the
processing step.
Each service will notify the Data Resource Center once it has completed
publishing its data.

Step 5: Completion
------------------

When all required services have notified the Data Resource Center of successful
publication, the release will be said to be published and available to end
users.
