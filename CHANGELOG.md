# Kids First Study Creator Change History

## Release 1.15.0

### Summary

- Emojis: ✨ x1, 🔧 x2, 🐛 x3, ⬆️ x2, 🐳 x1, 💄 x1
- Categories: Additions x1, Other Changes x3, Fixes x3, Ops x3

### New features and changes

- [#581](https://github.com/kids-first/kf-api-study-creator/pull/581) - ✨ Add investigator name to study - [7c147b2e](https://github.com/kids-first/kf-api-study-creator/commit/7c147b2e2da047961ca15380b8de58f9281557dd) by [dankolbman](https://github.com/dankolbman)
- [#580](https://github.com/kids-first/kf-api-study-creator/pull/580) - 🔧 Add flag to enabled/disable DR bucket creation - [428020b5](https://github.com/kids-first/kf-api-study-creator/commit/428020b5008050c2ed318176652c6b76d932bdd6) by [dankolbman](https://github.com/dankolbman)
- [#573](https://github.com/kids-first/kf-api-study-creator/pull/573) - 🔧 Add settings to status schema - [7c03defe](https://github.com/kids-first/kf-api-study-creator/commit/7c03defe4aa08212eebf9e64023953674150aa52) by [dankolbman](https://github.com/dankolbman)
- [#579](https://github.com/kids-first/kf-api-study-creator/pull/579) - 🐛 Fix bugs from switching to Debian image - [40cf58cd](https://github.com/kids-first/kf-api-study-creator/commit/40cf58cd4c6b65558127551b7eb563a0e4c0f1e3) by [znatty22](https://github.com/znatty22)
- [#578](https://github.com/kids-first/kf-api-study-creator/pull/578) - ⬆️ Bump boto3 and requests - [fa5896a0](https://github.com/kids-first/kf-api-study-creator/commit/fa5896a0364596583bfc2447af4fe7918d180b7a) by [znatty22](https://github.com/znatty22)
- [#577](https://github.com/kids-first/kf-api-study-creator/pull/577) - 🐳 Switch to python:3.8-slim-buster docker img - [3ca47fd7](https://github.com/kids-first/kf-api-study-creator/commit/3ca47fd70f491080195e937004dafdb98fb1663b) by [znatty22](https://github.com/znatty22)
- [#567](https://github.com/kids-first/kf-api-study-creator/pull/567) - 💄 Clean up release messages - [843f0bab](https://github.com/kids-first/kf-api-study-creator/commit/843f0bab5128902332359beaca9be3e8643fcee9) by [dankolbman](https://github.com/dankolbman)
- [#572](https://github.com/kids-first/kf-api-study-creator/pull/572) - ⬆️ Bump cryptography from 3.2 to 3.3.2 - [e046430d](https://github.com/kids-first/kf-api-study-creator/commit/e046430df6b9e75c4475b1d3e088428ab22f622a) by [dependabot[bot]](https://github.com/apps/dependabot)
- [#566](https://github.com/kids-first/kf-api-study-creator/pull/566) - 🐛 Only verify release id if its in the response - [d27077d9](https://github.com/kids-first/kf-api-study-creator/commit/d27077d98ae0e429a2c94a4428380053fdeb06ca) by [dankolbman](https://github.com/dankolbman)
- [#564](https://github.com/kids-first/kf-api-study-creator/pull/564) - 🐛 Add safeguards for trace sampler - [32e7f2e0](https://github.com/kids-first/kf-api-study-creator/commit/32e7f2e03d70463591260896a501c722825fddf2) by [dankolbman](https://github.com/dankolbman)


## Release 1.14.7

### Summary

- Emojis: 🐛 x2, 🔥 x2, ⬆️ x1, ✨ x1
- Categories: Fixes x2, Removals x2, Ops x1, Additions x1

### New features and changes

- [#515](https://github.com/kids-first/kf-api-study-creator/pull/515) - 🐛 Don't resolve downloadUrls if not enough info - [8dbae2a0](https://github.com/kids-first/kf-api-study-creator/commit/8dbae2a0691f978bf5c22b9b22ac7e064ca9c43d) by [dankolbman](https://github.com/dankolbman)
- [#514](https://github.com/kids-first/kf-api-study-creator/pull/514) - 🐛 Fix events query for non-admins - [9f2c9f81](https://github.com/kids-first/kf-api-study-creator/commit/9f2c9f817353218d175a658bb091c6199be7797b) by [dankolbman](https://github.com/dankolbman)
- [#511](https://github.com/kids-first/kf-api-study-creator/pull/511) - 🔥 Remove ego authentication - [f803ec54](https://github.com/kids-first/kf-api-study-creator/commit/f803ec5444120d5f49c6ec2d95a37406fc0e05f6) by [dankolbman](https://github.com/dankolbman)
- [#512](https://github.com/kids-first/kf-api-study-creator/pull/512) - 🔥 Remove hypothesis testing - [09b1a9ef](https://github.com/kids-first/kf-api-study-creator/commit/09b1a9ef66532f8b6d4f054231ec3ab101ec6e6f) by [dankolbman](https://github.com/dankolbman)
- [#496](https://github.com/kids-first/kf-api-study-creator/pull/496) - ⬆️ Bump cryptography from 2.5 to 3.2 - [709450f4](https://github.com/kids-first/kf-api-study-creator/commit/709450f4821e83eba793b5ddbdbf0bc5cefcc9bc) by [dependabot[bot]](https://github.com/apps/dependabot)
- [#509](https://github.com/kids-first/kf-api-study-creator/pull/509) - ✨ Kill rq jobs by id - [c747e001](https://github.com/kids-first/kf-api-study-creator/commit/c747e001e4a09d48ed60252f32a39aca29a9d7aa) by [znatty22](https://github.com/znatty22)


## Release 1.14.6

### Summary

- Emojis: ✨ x2
- Categories: Additions x2

### New features and changes

- [#494](https://github.com/kids-first/kf-api-study-creator/pull/494) - ✨ Add Genomic Workflow Output Manifest - [a9101a98](https://github.com/kids-first/kf-api-study-creator/commit/a9101a981ee0548eda6fcad4fba6906fcd070b67) by [znatty22](https://github.com/znatty22)
- [#482](https://github.com/kids-first/kf-api-study-creator/pull/482) - ✨ Job logs - [2bc60fd3](https://github.com/kids-first/kf-api-study-creator/commit/2bc60fd386d8c780f431e0b89b5e709920262d0d) by [dankolbman](https://github.com/dankolbman)


## Release 1.14.5

### Summary

- Emojis: 🐛 x1
- Categories: Fixes x1

### New features and changes

- [#483](https://github.com/kids-first/kf-api-study-creator/pull/483) - 🐛 Stringify before checking for printable chars - [eb43ec7c](https://github.com/kids-first/kf-api-study-creator/commit/eb43ec7c9fe9cc2e664c9077c5ca9b1243611090) by [dankolbman](https://github.com/dankolbman)


## Release 1.14.4

### Summary

- Emojis: 🔧 x1, ✨ x2
- Categories: Other Changes x1, Additions x2

### New features and changes

- [#480](https://github.com/kids-first/kf-api-study-creator/pull/480) - 🔧 Get stage from environment - [1bc3dfd7](https://github.com/kids-first/kf-api-study-creator/commit/1bc3dfd7f23a840234c7a8e673981e145f86507d) by [dankolbman](https://github.com/dankolbman)
- [#475](https://github.com/kids-first/kf-api-study-creator/pull/475) - ✨ New expedited types - [e89a4ae5](https://github.com/kids-first/kf-api-study-creator/commit/e89a4ae525d1406144359a6236af668c22adc85f) by [dankolbman](https://github.com/dankolbman)
- [#472](https://github.com/kids-first/kf-api-study-creator/pull/472) - ✨ Add download extract config endpoint - [d845e21c](https://github.com/kids-first/kf-api-study-creator/commit/d845e21cb0d3226191ba88cadbff58b401af4214) by [XuTheBunny](https://github.com/XuTheBunny)


## Release 1.14.3

### Summary

- Emojis: 📝 x1, 🔧 x1, 🐛 x1, ✨ x2
- Categories: Documentation x1, Other Changes x1, Fixes x1, Additions x2

### New features and changes

- [#473](https://github.com/kids-first/kf-api-study-creator/pull/473) - 📝 Expand upload documentation - [f9927c5d](https://github.com/kids-first/kf-api-study-creator/commit/f9927c5db9ed352e70df14469f6e688225f467ee) by [dankolbman](https://github.com/dankolbman)
- [#471](https://github.com/kids-first/kf-api-study-creator/pull/471) - 🔧 Migrated to standard deployment - [cc742eae](https://github.com/kids-first/kf-api-study-creator/commit/cc742eaed19bb2d7b21f658affc9b8af58934ca2) by [alubneuski](https://github.com/alubneuski)
- [#470](https://github.com/kids-first/kf-api-study-creator/pull/470) - 🐛 Fix referral token exceptions - [e8ad9d50](https://github.com/kids-first/kf-api-study-creator/commit/e8ad9d50afb8e9bd75a117ad3c92dd2fbbabaa92) by [dankolbman](https://github.com/dankolbman)
- [#468](https://github.com/kids-first/kf-api-study-creator/pull/468) - ✨ Valid types field - [354a8a66](https://github.com/kids-first/kf-api-study-creator/commit/354a8a6634b93d3f5a3a8a4fa73031ebbe465bdc) by [dankolbman](https://github.com/dankolbman)
- [#467](https://github.com/kids-first/kf-api-study-creator/pull/467) - ✨ Document file_type validation - [dfdbbece](https://github.com/kids-first/kf-api-study-creator/commit/dfdbbeceabf91accdabd6fdec0e29d18cbb8373d) by [dankolbman](https://github.com/dankolbman)


## Release 1.14.2

### Summary

- Emojis: 🐛 x1
- Categories: Fixes x1

### New features and changes

- [#459](https://github.com/kids-first/kf-api-study-creator/pull/459) - 🐛 Check view_my_version permissions for downloads - [6a8cad5d](https://github.com/kids-first/kf-api-study-creator/commit/6a8cad5d42e505a72965157ef7b12782e366bd1b) by [dankolbman](https://github.com/dankolbman)


## Release 1.14.1

### Summary

- Emojis: 🐛 x1, ♻️ x1, ✨ x2, 🔧 x2, 🔥 x1
- Categories: Fixes x1, Other Changes x3, Additions x2, Removals x1

### New features and changes

- [#457](https://github.com/kids-first/kf-api-study-creator/pull/457) - 🐛 Determine study from version or file - [642c1aef](https://github.com/kids-first/kf-api-study-creator/commit/642c1aef4c47d0d37ee6147c8742affc59d31346) by [dankolbman](https://github.com/dankolbman)
- [#455](https://github.com/kids-first/kf-api-study-creator/pull/455) - ♻️ Refactor document upload flow - [f825f582](https://github.com/kids-first/kf-api-study-creator/commit/f825f582caede302a14493532bd5510a11905772) by [dankolbman](https://github.com/dankolbman)
- [#456](https://github.com/kids-first/kf-api-study-creator/pull/456) - ✨ Accept .xls file type for file analysis - [c76d4d4c](https://github.com/kids-first/kf-api-study-creator/commit/c76d4d4c360ca84467467ebad9f767558e66a3ec) by [XuTheBunny](https://github.com/XuTheBunny)
- [#454](https://github.com/kids-first/kf-api-study-creator/pull/454) - 🔧 Dev Ops upgrades - [21e2d4a8](https://github.com/kids-first/kf-api-study-creator/commit/21e2d4a8b277adf23dc058af111c8f9cdb54542e) by [dankolbman](https://github.com/dankolbman)
- [#452](https://github.com/kids-first/kf-api-study-creator/pull/452) - 🔧 Add SSL setting to RQ config - [03fd0c53](https://github.com/kids-first/kf-api-study-creator/commit/03fd0c53d7e2cb97d1fbf6ffed9f1538ea5c362f) by [dankolbman](https://github.com/dankolbman)
- [#449](https://github.com/kids-first/kf-api-study-creator/pull/449) - ✨ File analyses - [c2e5a87c](https://github.com/kids-first/kf-api-study-creator/commit/c2e5a87c67a780c1740f5bdbfbd527b47aef1172) by [dankolbman](https://github.com/dankolbman)
- [#450](https://github.com/kids-first/kf-api-study-creator/pull/450) - 🔥 Remove vault - [4d6dc934](https://github.com/kids-first/kf-api-study-creator/commit/4d6dc93464cfc515a86ec0115380c2f4ecdc8eea) by [dankolbman](https://github.com/dankolbman)


## Release 1.14.0

### Summary

- Emojis: 🐛 x2, ♻️ x3, ✅ x2, 🔧 x1, ✨ x1
- Categories: Fixes x2, Other Changes x6, Additions x1

### New features and changes

- [#433](https://github.com/kids-first/kf-api-study-creator/pull/433) - 🐛 Fix file link in slack updates - [4266f2ff](https://github.com/kids-first/kf-api-study-creator/commit/4266f2ff97c984a944253bb6db24786081016ae6) by [XuTheBunny](https://github.com/XuTheBunny)
- [#446](https://github.com/kids-first/kf-api-study-creator/pull/446) - ♻️ Replace usernames in events with full names - [c9d459b5](https://github.com/kids-first/kf-api-study-creator/commit/c9d459b563052db4a461eafdf8043cef766de73a) by [XuTheBunny](https://github.com/XuTheBunny)
- [#444](https://github.com/kids-first/kf-api-study-creator/pull/444) - ✅ Add test for model strings - [2b02f77c](https://github.com/kids-first/kf-api-study-creator/commit/2b02f77caefda6adeb182aca82d1e6f4d87c0714) by [dankolbman](https://github.com/dankolbman)
- [#445](https://github.com/kids-first/kf-api-study-creator/pull/445) - ♻️ Refactor schemas - [faf2d40e](https://github.com/kids-first/kf-api-study-creator/commit/faf2d40e9e12ad3e2d87473d07b9538b162c9f39) by [dankolbman](https://github.com/dankolbman)
- [#443](https://github.com/kids-first/kf-api-study-creator/pull/443) - ✅ Add test for unfound nodes - [d47e2a4d](https://github.com/kids-first/kf-api-study-creator/commit/d47e2a4d52fcfa0aeaf1603e4653d2152d586434) by [dankolbman](https://github.com/dankolbman)
- [#442](https://github.com/kids-first/kf-api-study-creator/pull/442) - 🔧 Increase task queue timeouts - [013dd82e](https://github.com/kids-first/kf-api-study-creator/commit/013dd82e108689f7172e179e8eb0f9598e9d16ac) by [dankolbman](https://github.com/dankolbman)
- [#437](https://github.com/kids-first/kf-api-study-creator/pull/437) - ♻️ Shift slack messages timestamp to be US/Eastern timezone - [ade30200](https://github.com/kids-first/kf-api-study-creator/commit/ade30200164cf74f716f9f174f1d5719f3fb6fa0) by [XuTheBunny](https://github.com/XuTheBunny)
- [#438](https://github.com/kids-first/kf-api-study-creator/pull/438) - ✨ Specify what change was made to a document in event message - [64827099](https://github.com/kids-first/kf-api-study-creator/commit/64827099141cbeefb1fabd8ece1055d85a519378) by [XuTheBunny](https://github.com/XuTheBunny)
- [#439](https://github.com/kids-first/kf-api-study-creator/pull/439) - 🐛 Fix referral token event message with f-string - [06be0109](https://github.com/kids-first/kf-api-study-creator/commit/06be010969f20ebe7195dd40121ea5169587402b) by [XuTheBunny](https://github.com/XuTheBunny)


## Release 1.13.0

### Summary

- Emojis: ✨ x2, 🗃️ x1
- Categories: Additions x2, Other Changes x1

### New features and changes

- [#429](https://github.com/kids-first/kf-api-study-creator/pull/429) - ♻️ Separate update version permission to change meta and change status - [de1ed7ff](https://github.com/kids-first/kf-api-study-creator/commit/de1ed7ff89044c0375782f54897e29ba6d53b9f2) by [XuTheBunny](https://github.com/XuTheBunny)
- [#428](https://github.com/kids-first/kf-api-study-creator/pull/428) - Add file and collaborator details to slack notification - [589ee225](https://github.com/kids-first/kf-api-study-creator/commit/589ee225dca8a21b5b4c0ad961394825ddaf91a1) by [XuTheBunny](https://github.com/XuTheBunny)
- [#426](https://github.com/kids-first/kf-api-study-creator/pull/426) - 🗃️ Patch collaborator mutation - [87babf80](https://github.com/kids-first/kf-api-study-creator/commit/87babf80c8b4a8443a38a6e5a718f68f30502a58) by [dankolbman](https://github.com/dankolbman)
- [#423](https://github.com/kids-first/kf-api-study-creator/pull/423) - Collaborator roles - [79895186](https://github.com/kids-first/kf-api-study-creator/commit/7989518635bebd162d797867011552dd578ddd2a) by [dankolbman](https://github.com/dankolbman)

## Release 1.12.0

### Summary

- Emojis: 🔥 x1, ♻️ x1
- Categories: Removals x1, Other Changes x1

### New features and changes

- [#424](https://github.com/kids-first/kf-api-study-creator/pull/424) - 🔥 Remove default Cavatica projects for new studies - [958a1823](https://github.com/kids-first/kf-api-study-creator/commit/958a18234ca8066a531858a61a5d777c5382ba93) by [XuTheBunny](https://github.com/XuTheBunny)
- [#422](https://github.com/kids-first/kf-api-study-creator/pull/422) - ♻️ Improve verbosity of collaborator events - [4a387f40](https://github.com/kids-first/kf-api-study-creator/commit/4a387f40e7e2f7f36f1472fe33e1e45d74689972) by [XuTheBunny](https://github.com/XuTheBunny)

## Release 1.11.1

### Summary

- Emojis: 📈 x1, ♻️ x1, 🔊 x1, ⬆️ x1
- Categories: Additions x2, Other Changes x1, Ops x1

### New features and changes

- [#420](https://github.com/kids-first/kf-api-study-creator/pull/420) - 📈 Add utm tracking to slack pins - [ab620d52](https://github.com/kids-first/kf-api-study-creator/commit/ab620d521558e9d1029964664449609b0879702c) by [dankolbman](https://github.com/dankolbman)
- [#419](https://github.com/kids-first/kf-api-study-creator/pull/419) - ♻️ Auto join Slack channels - [abd9b8a4](https://github.com/kids-first/kf-api-study-creator/commit/abd9b8a4dbec407497f00b0929e25a88ee73ca03) by [dankolbman](https://github.com/dankolbman)
- [#415](https://github.com/kids-first/kf-api-study-creator/pull/415) - 🔊 Task logging - [9761799d](https://github.com/kids-first/kf-api-study-creator/commit/9761799d4451717d5de31c4e5ef64437c91c9a64) by [dankolbman](https://github.com/dankolbman)
- [#414](https://github.com/kids-first/kf-api-study-creator/pull/414) - ⬆️ Bump django from 2.2.10 to 2.2.13 - [7e96cd57](https://github.com/kids-first/kf-api-study-creator/commit/7e96cd57e80f782fbb21eee7346f98610bb858c3) by [dependabot[bot]](https://github.com/apps/dependabot)

## Kids First Study Creator Release Release 1.11.0

Add email invites for new and existing users.

### Summary

- Emojis: 🖼 x2, ✏️ x1, 📦 x1, 🐛 x4, 🔧 x1, ✨ x3
- Categories: Other Changes x3, Fixes x5, Ops x1, Additions x3

### New features and changes

- [#412](https://github.com/kids-first/kf-api-study-creator/pull/412) - 🖼 Shrink email header image - [20bd8398](https://github.com/kids-first/kf-api-study-creator/commit/20bd8398e8787a614374081d212666278a2ec49a) by [dankolbman](https://github.com/dankolbman)
- [#411](https://github.com/kids-first/kf-api-study-creator/pull/411) - ✏️ Correct typo in email - [9b3f6bdb](https://github.com/kids-first/kf-api-study-creator/commit/9b3f6bdb80fdd2d8d7fced16abaec363ef544c30) by [dankolbman](https://github.com/dankolbman)
- [#409](https://github.com/kids-first/kf-api-study-creator/pull/409) - 📦 Use SES email backend - [28a9370b](https://github.com/kids-first/kf-api-study-creator/commit/28a9370b68b2d093ec3467e216e86f0c268d8a86) by [dankolbman](https://github.com/dankolbman)
- [#408](https://github.com/kids-first/kf-api-study-creator/pull/408) - 🖼 Update email picture - [734c6d02](https://github.com/kids-first/kf-api-study-creator/commit/734c6d021010f9c6cd58242af2f40eb5de267e92) by [dankolbman](https://github.com/dankolbman)
- [#407](https://github.com/kids-first/kf-api-study-creator/pull/407) - 🐛 Use proper email settings - [4f6b6600](https://github.com/kids-first/kf-api-study-creator/commit/4f6b6600669d5e6b0f0ec6d659f81d9277d227b7) by [dankolbman](https://github.com/dankolbman)
- [#406](https://github.com/kids-first/kf-api-study-creator/pull/406) - 🐛 Fix email settings - [df8b6582](https://github.com/kids-first/kf-api-study-creator/commit/df8b6582e86a9211b181d759e6f20dcebba18b0f) by [dankolbman](https://github.com/dankolbman)
- [#405](https://github.com/kids-first/kf-api-study-creator/pull/405) - 🐛 Don't overwrite studies after invite - [b6e5e350](https://github.com/kids-first/kf-api-study-creator/commit/b6e5e35009585cf7a1f741bebf5f11f201f1f5d2) by [dankolbman](https://github.com/dankolbman)
- [#404](https://github.com/kids-first/kf-api-study-creator/pull/404) - 🔧 Add slack job - [130c4538](https://github.com/kids-first/kf-api-study-creator/commit/130c4538094644ceddb360a2e9f3b621a509147c) by [dankolbman](https://github.com/dankolbman)
- [#402](https://github.com/kids-first/kf-api-study-creator/pull/402) - ✨ Add slack_notify field to study model default to true - [d2a9b91d](https://github.com/kids-first/kf-api-study-creator/commit/d2a9b91d92703dc1ef2d676433536f3b52beb7e9) by [XuTheBunny](https://github.com/XuTheBunny)
- [#401](https://github.com/kids-first/kf-api-study-creator/pull/401) - 🐛 Use https for codecov - [2386af5d](https://github.com/kids-first/kf-api-study-creator/commit/2386af5dccb7fb2b0356c88d1fb78d5a9bbe781c) by [dankolbman](https://github.com/dankolbman)
- [#398](https://github.com/kids-first/kf-api-study-creator/pull/398) - ✨ Add ReferralToken Model and create referral tokens mutation - [4e47c312](https://github.com/kids-first/kf-api-study-creator/commit/4e47c312b93c933a67672f420dceaaab9c0fb354) by [XuTheBunny](https://github.com/XuTheBunny)
- [#397](https://github.com/kids-first/kf-api-study-creator/pull/397) - ✨ Add email configuration - [c79685cb](https://github.com/kids-first/kf-api-study-creator/commit/c79685cb4fbd6f9cfd426dc24edb8ee3e3d1e398) by [dankolbman](https://github.com/dankolbman)

# Kids First Study Creator Release 1.10.0

## Features

Add study status columns

### Summary

Feature Emojis: ✨x3
Feature Labels: [feature](https://api.github.com/repos/kids-first/kf-api-study-creator/labels/feature) x3

### New features and changes

- (#392) ✨ Add phenotype status to study - @XuTheBunny
- (#391) ✨ Add ingestion status to study - @XuTheBunny
- (#388) ✨ Sequencing status - @dankolbman

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