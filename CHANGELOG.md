# Kids First Study Creator Release 1.9.0

## Features

Overhaul of user permissions.

### Summary

Feature Emojis: ✨x5 🔒x5 🐛x3 ♻️x2 🐋x1 📝x1 🐳x1 🔧x1
Feature Labels: [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x10 [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x5 [refactor](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/refactor) x5 [devops](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/devops) x2 [documentation](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/documentation) x2

### New features and changes

- (#389) 🐛 Make fake data reproducible - @dankolbman
- (#382) ✨ Idempotent test files - @dankolbman
- (#381) ♻️ Refactor the permission checking for uploading version - @XuTheBunny
- (#379) 🐋 Add coordinator service - @dankolbman
- (#378) 🐛 Create test user before fake data - @dankolbman
- (#377) ✨ Idempotent factories - @dankolbman
- (#376) ✨ Add development endpoint to settings schema - @dankolbman
- (#373) ✨ Add development endpoints - @dankolbman
- (#375) 🔒 Add permissions to study mutations - @dankolbman
- (#374) 🔒 Add change study permission to Admin group - @XuTheBunny
- (#372) 🔒 Add create study permission - @dankolbman
- (#371) 📝 Update permission docs - @dankolbman
- (#370) 🔒 Cavatica permissions - @dankolbman
- (#359) 🔒 Authorization model - @dankolbman
- (#364) 🐳 Build and push images to Dockerhub registry - @dankolbman
- (#365) ✨ Add DBG file type for dbGaP Submission File - @XuTheBunny
- (#362) 🔧 Use static seed when creating fake data - @dankolbman
- (#355) 🐛 Use id as primary key for users - @dankolbman
- (#358) ♻️ Hard-code https scheme for downloads - @dankolbman

# Kids First Study Creator Release 1.8.0

## Features

Add bucket models and tags to documents.

### Summary

Feature Emojis: ✨x5 🐛x1 ♻️x1
Feature Labels: [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x6 [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x1 [refactor](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/refactor) x1

### New features and changes

- (#354) 🐛 Allow files to be updated with no tags - @dankolbman
- (#353) ♻️ Refactor collaborator mutations - @dankolbman
- (#351) ✨ Bucket sync task - @dankolbman
- (#350) ✨ Add bucket models - @dankolbman
- (#345) ✨ Add collaborators to studies - @dankolbman
- (#342) ✨ Consolidate bucket service - @dankolbman
- (#344) ✨ Add tags field to file model and allow updating - @XuTheBunny

# Kids First Study Creator Release 1.7.4

## Features

Hot fix to correct a test that fails for tagged branches.

### Summary

Feature Emojis: 🚑x1
Feature Labels: [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x1

### New features and changes

- (#338) 🚑 Version test hotfix - @dankolbman

# Kids First Study Creator Release 1.7.3

## Features

Adds task scheduler and status queries for exposing configuration.

### Summary

Feature Emojis: ✨x7 🐳x3 📝x2 ⬆️x1 🔧x1
Feature Labels: [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x7 [devops](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/devops) x3 [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x2 [documentation](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/documentation) x2 [refactor](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/refactor) x1

### New features and changes

- (#336) ✨ Add Dataservice sync job - @dankolbman
- (#334) ✨ Import volume files - @dankolbman
- (#333) ✨ Add scheduled tasks - @dankolbman
- (#328) ✨ Allow users to specify and name research projects on creation - @XuTheBunny
- (#330) ✨ Features in status - @dankolbman
- (#329) ⬆️ Bump psycopg2 to 2.8.4 - @dankolbman
- (#325) 📝 Update localhost port to 5002 and add description for use roles - @XuTheBunny
- (#322) 🐳 Add postgresql client as persistent dep - @dankolbman
- (#321) 🐳 Use alpine image - @dankolbman
- (#320) 🐳 Install postgres in base image - @dankolbman
- (#319) ✨ Add status query - @dankolbman
- (#318) ✨ Run study setup in tasks - @dankolbman
- (#316) 🔧 Make sub the primary user id - @dankolbman
- (#317) 📝 Add documentation for Auth0 configuration - @dankolbman

# Kids First Study Creator Release 1.7.2

## Features

Add user setting for email preference.
Setup Cavatica volumes for new projects.

### Summary

Feature Emojis: ✨x2 ✅x1 🐛x1
Feature Labels: [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x2 [devops](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/devops) x1 [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x1

### New features and changes

- (#287) ✨ Attach Cavatica volumes - @dankolbman
- (#313) ✅ Add Codecov test as default pull request checking method - @XuTheBunny
- (#312) 🐛 Fix the user email/slack notify toggle mutation - @XuTheBunny
- (#311) ✨ Add email notification field - @dankolbman

# Kids First Study Creator Release 1.7.1

## Features

Hot fix to un-delete studies that have reappeared in dataservice and stop trying to configure Cavatica projects' type on sync.

### Summary

Feature Emojis: ♻️x2
Feature Labels: [refactor](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/refactor) x1

### New features and changes

- (#308) ♻️ Don't set project type based on project name - @dankolbman
- (#309) ♻️ Un-delete studies that have reappeared - @dankolbman

# Kids First Study Creator Release 1.7.0

## Features

### Summary

Feature Emojis: ✨x5 🔧x2 📝x1
Feature Labels: [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x5 [devops](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/devops) x3 [documentation](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/documentation) x1 [refactor](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/refactor) x1

### New features and changes

- (#306) ✨ Add updateProject mutation - @dankolbman
- (#304) 📝 Add page on Data Service settings - @dankolbman
- (#300) ✨ Integrate bucketservice - @dankolbman
- (#302) Terraform 0.12 Upgrade - @blackdenc
- (#296) 🔧 Update port for study creator - @dankolbman
- (#298) 🔧 Load database creds from S3 - @dankolbman
- (#294) ✨ Make bucket modifiable - @dankolbman
- (#293) ✨ Mark studies as deleted from dataservice - @dankolbman
- (#291) ✏️ Rename datetime filters - @dankolbman
- (#289) ✨ Emit events for projects - @dankolbman

# Kids First Study Creator Release 1.6.1

## Features

Makes request timeouts configurable.

### Summary

Feature Emojis: 🔧x1 ✨x1
Feature Labels: [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x2

### New features and changes

- (#284) 🔧 Make requests timout configurable - @dankolbman
- (#283) ✨ Add project study filter - @dankolbman

# Kids First Study Creator Release 1.6.0

## Features

Introduces study creation and Cavatica project automation features.

### Summary

Feature Emojis: ✨x20 🐛x7 📝x3 ⬆️x3 ♻️x2 🔧x2 🐳x2 👷x1 🗃x1 🔥
Feature Labels: [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x19 [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x11 [refactor](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/refactor) x8 [devops](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/devops) x4 [documentation](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/documentation) x3

### New features and changes

- (#280) ✨ Add overrides for user's roles and groups - @dankolbman
- (#278) 🐛 Fix datetime issues - @dankolbman
- (#279) ♻️ Use ID type for study argument in createProject mutation - @dankolbman
- (#276) ✨ Add createProject mutation - @dankolbman
- (#273) ✨ Copy users into new projects - @dankolbman
- (#274) ✨ Make event subqueries filterable - @dankolbman
- (#272) ✨ Make projects sortable - @dankolbman
- (#268) 🐛 Replace workflow type enum underscores - @dankolbman
- (#259) 👷 Load cavatica secrets to environment - @dankolbman
- (#267) ✨ Mark projects as deleted on sync - @dankolbman
- (#266) 🗃 Add migration to adjust workflow choices - @dankolbman
- (#264) ✨ Add workflows argument to createStudy mutation - @dankolbman
- (#262) 📝 Input docs - @dankolbman
- (#261) 🐛 Add release date to mutations - @dankolbman
- (#260) 🐛 Fix study createdAt date parsing - @XuTheBunny
- (#258) ✨ Add unlinkProject mutation - @dankolbman
- (#256) 🐛 Make Cavatica times timezone aware - @dankolbman
- (#255) ✨ Add linkProject mutation - @dankolbman
- (#254) 🔧 Remove default Cavatica token settings - @dankolbman
- (#253) 📝 Add page about Cavatica integration - @dankolbman
- (#252) ✨ Create events when studies are created - @dankolbman
- (#251) 📝 Add descriptions to all queries - @dankolbman
- (#249) ✨ New study fields - @dankolbman
- (#250) ✨ Add sync projects mutation - @XuTheBunny
- (#245) 🔥 Remove batches - @dankolbman
- (#244) ✨ Study description - @dankolbman
- (#243) 🐛 Fix project creation error with naming - @XuTheBunny
- (#240) ♻️ Rename event filter arguments - @dankolbman
- (#238) ✨ Add release date to study - @dankolbman
- (#242) ✨ Add workflow_type field to project model - @XuTheBunny
- (#229) ✨ Create new projects in Cavatica on study creation - @XuTheBunny
- (#235) ⬆️ Bump up moto to version 1.3.10 - @XuTheBunny
- (#234) 🐳 Fix docker environment formatting - @XuTheBunny
- (#227) ✨ Create CavaticaProject model - @XuTheBunny
- (#226) ⬆️ Bump django from 2.1.10 to 2.1.11 - @dependabot[bot]
- (#225) ✨ Add updateStudy mutation - @dankolbman
- (#223) 🐛 Don't try to recreate dev user - @dankolbman
- (#224) 🐳 Use common postgres versions for containers - @dankolbman
- (#219) ✨Add integration with dataservice for new studies - @dankolbman
- (#215) 🔧 Authenticate requests as admin for development - @dankolbman
- (#214) ✨ Add filter by file kf_id to allVersions - @dankolbman
- (#210) ⬆️ Bump django from 2.1.9 to 2.1.10 - @dependabot[bot]

# Kids First Study Creator Release 1.5.0

## Features

### Summary

Feature Emojis: 📝x1 ⬆️x1 🐛 x1
Feature Labels: [documentation](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/documentation) x1 [devops](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/devops) x1 [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x1

### New features and changes

- (#208) 📝 Update docs - @dankolbman
- (#207) ⬆️ Bump django from 2.1.7 to 2.1.9 - @dependabot[bot]
- (#206) 🐛 raises study short_name character limit to 500 - @bdolly

# Kids First Study Creator Release 1.4.0

## Features

Add user profiles with notification settings and event tracking.

### Summary

Feature Emojis: ✨x6 🐛x2 ♻️ x1
Feature Labels: [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x6 [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x2 [refactor](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/refactor) x1

### New features and changes

- (#200) ✨ Add creator field to tokens - @dankolbman
- (#198) ✨ Add events - @dankolbman
- (#197) ✨ Add user notification settings - @dankolbman
- (#194) ✨ Add myProfile query - @dankolbman
- (#193) ♻️ Split file and version upload mutations - @dankolbman
- (#192) 🐛 Use version file_name for downloads - @dankolbman
- (#191) ✨ Add creator field to files and versions - @dankolbman
- (#188) 🐛 No service users - @dankolbman
- (#185) ✨ Save users to database - @dankolbman

# Kids First Study Creator Release 1.3.0

## Features

Adds new features for file version uploads.

### Summary

Feature Emojis: ✨x4 ✏️x1 ♻️x1 🔧 x1
Feature Labels: [refactor](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/refactor) x4 [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x3

### New features and changes

- (#182) ✨ Add version file_name field - @dankolbman
- (#172) ✨ Version state field - @dankolbman
- (#170) ✨ Add descriptions to versions - @dankolbman
- (#168) ✏️ Rename objects - @dankolbman
- (#166) ♻️ Reorganize tests - @dankolbman
- (#164) 🔧 Increase max description length - @dankolbman
- (#157) ✨ Version uploads - @dankolbman

# Kids First Study Creator Release 1.2.1

## Features

Small field addition to enable cache refreshes on the UI client.

### Summary

Feature Emojis: ♻️x1
Feature Labels: [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x1

### New features and changes

- (#153) ♻️ Return kf_id from delete file mutation - @dankolbman

# Kids First Study Creator Release 1.2.0

## Features

Introduces minor bug fixes and security features.

### Summary

Feature Emojis: 🐛x3 ✨x2 🙈x1
Feature Labels: [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x4 [devops](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/devops) x1 [refactor](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/refactor) x1 [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x1

### New features and changes

- (#150) 🙈 Ignore gh-pages in CircleCI - @dankolbman
- (#147) ✨ Read once tokens - @dankolbman
- (#149) 🐛 Return 401 when not authed for download - @dankolbman
- (#146) 🐛 Use utf-8 encoding for Content-Disposition - @dankolbman
- (#145) 🐛 Add Content-Type header to downloads - @dankolbman
- (#143) ✨ Look for tokens in Authorization header - @dankolbman

# Kids First Study Creator Release 1.1.0

Added new authentication through auth0, developer download tokens, signed
download urls, and service tokens.

## Features

### Summary

Feature Emojis: ✨x8 ♻️x1 🔥x1 🗃x1 🚨x1 📝 Updatex1 x1
Feature Labels: [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x7 [refactor](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/refactor) x4 [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x2 [documentation](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/documentation) x1

### New features and changes

- (#138) ✨ Add developer tokens - @dankolbman
- (#136) ✨ Add deleteFile mutation - @dankolbman
- (#135) ✨ Add file type to update mutation - @dankolbman
- (#134) ✨ Service token auth - @dankolbman
- (#132) ♻️ Cache JWKS for future validation - @dankolbman
- (#130) 🔥 Remove django admin - @dankolbman
- (#129) ✨ Add mutation to make signed url - @dankolbman
- (#128) ✨ Require study id in download to be valid - @dankolbman
- (#125) ✨ Signed download urls - @dankolbman
- (#120) ✨ Add auth0 - @dankolbman
- (#117) 🗃 Add missing migration - @dankolbman
- (#116) 🚨 Add pycodestyle - @dankolbman
- (#113) 📝Update uploads page - @znatty22
- (#109) Release 1.0.0 - @dankolbman

# Kids First Study Creator Release 1.0.0

First release of the Kids First Study Creator.

### Summary

Feature Emojis: ✨x17 ♻️x11 🐛x7 📝x5 🔧x5 ✨Addx4 🐳x1 👷x1 ✏️x1 🐘x1 🗃x1 🚨x1 📄x1 🎉x1
Feature Labels: [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x26 [refactor](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/refactor) x13 [bug](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/bug) x10 [documentation](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/documentation) x8 [devops](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/devops) x1

### New features and changes

- (#108) 🐛 Fix public key problems - @dankolbman
- (#107) 🐳 Add service to kf-data-stack network - @znatty22
- (#106) ✨ JWT key validation - @dankolbman
- (#105) ♻️ Refactor download error - @XuTheBunny
- (#103) ✨Add download auth checking - @XuTheBunny
- (#101) ♻️ Update documentation for Uploading with GraphQL - @XuTheBunny
- (#92) ✨ Get entities by kf id - @dankolbman
- (#99) ♻️ Refactor download function - @XuTheBunny
- (#98) ♻️ Reformat file name - @XuTheBunny
- (#94) ✨Add version download field - @XuTheBunny
- (#93) 📝 Update documentation for permissions - @XuTheBunny
- (#91) ✨Add file mutation - @XuTheBunny
- (#89) ✨ Upload error handling - @XuTheBunny
- (#88) 🐛 Sync bucket names - @dankolbman
- (#83) 🔧 Load PRELOAD_DATA from env - @dankolbman
- (#82) ♻️ Increate upload file size limitation to 537M - @XuTheBunny
- (#80) ♻️ Refactor test by adding prep-file fixture - @XuTheBunny
- (#79) ✨ Sync studies from dataservice - @dankolbman
- (#81) 🔧 Display graphiql on site root - @dankolbman
- (#76) 🔧 Bypass authentication in development - @dankolbman
- (#73) 🐛 Don't create admin if already exists - @dankolbman
- (#72) 🐛 Installs psycopg2-binary - @dankolbman
- (#71) 🔧 Split settings files - @dankolbman
- (#68) ✨ File ids - @dankolbman
- (#67) ✨ Add version download endpoint - @XuTheBunny
- (#66) ✨ Add permission checking to allVersions query - @XuTheBunny
- (#65) ✨ Add permission checking to allFiles query - @XuTheBunny
- (#55) 👷 Add Jenkinsfile - @dankolbman
- (#61) ✨ Add manager for custom user model - @dankolbman
- (#56) 🐛 Take kwargs on study resolver - @dankolbman
- (#54) ✨ Add upload authorization - @XuTheBunny
- (#51) ✨ Add Ego JWT authentication - @dankolbman
- (#53) ✨ Add download field to GraphQL data response - @XuTheBunny
- (#50) ♻️ Refactor to use upload_file fixture - @XuTheBunny
- (#49) ✨ Set max upload file size - @XuTheBunny
- (#48) ✨ Add download endpoint - @XuTheBunny
- (#47) ♻️ Add dev stage to Dockerfile - @dankolbman
- (#46) ✏️ Change manifest file type enum - @XuTheBunny
- (#44) 🐛 Increase study name field max length to 500 - @XuTheBunny
- (#43) 🐘 Switch to PostgreSQL - @dankolbman
- (#42) 🗃 Add new study fields - @XuTheBunny
- (#40) ♻️ Add file to createFile response - @XuTheBunny
- (#39) 🐛 Rename batch to study - @XuTheBunny
- (#33) ✨ S3 Uploads - @dankolbman
- (#32) ✨ Add dotenv - @XuTheBunny
- (#31) ♻️ Rename FileEssence to File - @XuTheBunny
- (#30) 🔧 Exempt csrf from graphql endpoint - @XuTheBunny
- (#28) ♻️ Relate Files to Studies instead of batches - @dankolbman
- (#27) ✨ Add cors-headers package - @XuTheBunny
- (#19) 🚨Add Pep8 linting - @XuTheBunny
- (#18) ✨File upload - @XuTheBunny
- (#8) 📝 Base docs - @dankolbman
- (#7) 📝 Add docs site - @dankolbman
- (#6) 📝 Add README header - @dankolbman
- (#5) 📄 Add LICENSE - @dankolbman
- (#4) 🎉 Base GraphQL API - @dankolbman
- (#2) 📝 Add design doc for uploads - @dankolbman
