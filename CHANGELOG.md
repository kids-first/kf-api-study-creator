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
- (#132) ♻️  Cache JWKS for future validation - @dankolbman
- (#130) 🔥 Remove django admin - @dankolbman
- (#129) ✨ Add mutation to make signed url - @dankolbman
- (#128) ✨ Require study id in download to be valid - @dankolbman
- (#125) ✨ Signed download urls - @dankolbman
- (#120) ✨ Add auth0 - @dankolbman
- (#117) 🗃 Add missing migration - @dankolbman
- (#116) 🚨 Add pycodestyle - @dankolbman
- (#113) 📝Update uploads page - @znatty22
- (#109)  Release 1.0.0 - @dankolbman

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
