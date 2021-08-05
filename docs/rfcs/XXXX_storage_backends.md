# Storage Backends

**Status:** Approved, waiting for implementation


## Background and Existing Solution

![enter image description here](https://i.ibb.co/C7bzPNZ/storage-layout.png)
> A simple representation of how the application and its resources are currently allocated.

The the application relies on a data storage system to both save files that it receives and to account for other files that have been deposited externally. The current method that is used is adequate for a single tenant operating in a single AWS account, but needs to be re-thought for multiple tenants that  have more sophisticated storage needs.

### Study Buckets

Studies are central entities in the the application. They partition data that is collected and submitted by different research projects and investigators. For this reason, it was determined that each study would have its own bucket to segment it from other collections of data.

#### Creation

The the application automatically creates and configures buckets upon creation of a new study. These buckets are created in the same account as the IAM role that the API uses (Kids First Open Data). This account happens to be different from the account where the API actually resides (Kids First STRIDES). This is necessary as compute used to be contained within Kids First Open Data but was migrated to the STRIDES account. However, the data did not move and the codebase required that the IAM used was owned by the same account as the data.

#### Configuration

Each study bucket needs to be configured with the correct security policies, encryption, replication, logging, and so on. For this reason, the bucket creation process was automated and included as part of the the application's service offerings. Upon creation, the the application will configure these additional settings ensuring all buckets are setup correctly.

#### Layout
Each study bucket has a similar layout:
```
source/
  uploads/
harmonized/
```

Under `source` are data files such as raw read files received from the sequencing center, MRI DICOMs from the investigator, and so forth. The `uploads` directory contains files that are uploaded from the the application. `harmonized` contains files that were processed by the BIX team using things such as a standard alignment workflow or calling pipeline.

### Issues with Study Buckets

Study buckets are restricted to the same account as the IAM profile assigned to the application's compute instance.
The IAM profile contains a large surface of permissions needed to create and modify buckets.

## Storage Backend Solution
By allowing users to create "Storage Backends" that grant the application access to bucket resources in other accounts, we will be able to provide more flexibility in how organizations choose to store their data.

## Default Storage
![enter image description here](https://i.ibb.co/vBb1YsN/storage-layout.png)
"Default Storage" will refer to the defaults for how a new organization and its studies will be stored. It's important that new organizations and studies be quickly bootstraped into a working state without unnecessary configuration. To achieve this, the application will provide a default workspace for documents to land. This will be achieved by providing a Storage Backend that will point to the application's application bucket.

### Application Bucket

It's proposed that the application maintain a single bucket in which it may stash data. This bucket will be intended to contain anything the the application may need to store such as configuration files, user avatars, and similar. Most notably, though, it will contain uploaded documents for each study. In this way, the single application bucket will deprecate the need for each study bucket to contain its uploads. However, it is also recognized that perhaps some organizations may wish their uploaded documents to reside within their own resource pool. For this case, we will allow the document bucket to be specified within a different account.
The default solution for a new organization (and the existing Kids First organization) will be to store all documents within the application bucket. These documents will be kept as outlined above in the `New Layout` where the `studies/` prefix will be at the root of the bucket.

### New Layout

The layout of files uploaded by the application is outlined below. This structure will ultimately be placed within the storage backend's bucket under the provided prefix:
```
dewrangle/
	studies/
		SD_00000000/
			source/
			uploads/
			harmonized/
```

## External Storage Backends

![enter image description here](https://i.ibb.co/PTPMLnf/storage-layout.png)
When/ an organization requires all of their uploads or data files to be under their control, an organization administrator may specify credentials and details for a bucket of their choosing in a different account.

### Storage Backends

A Storage Backend is a simple entity that belongs to an organization and specifies IAM user credentials, a bucket that the IAM user has access to, and a prefix within that bucket. This concept will allow the application to access buckets across different accounts for the purpose of storing or evaluating files.

### Configuration

To configure a storage backend, an organization administrator will be required to provide details about the AWS account where their target bucket resides and a user who may access it. An organization administrator will be able to configure this by navigating to the *Organization Settings* screen and choosing *Storages*. This will allow the administrator to add a new storage by first asking the user to create a new IAM user in their AWS account and assigning a specified policy. After the user has done this, they will be required to provide the AWS access and secret key pair so that the application may access the bucket. The final step will be to allow the user to specify the bucket and what prefix under it they would like this storage backend to use as the root. After confirming their choices, the application will attempt to access the bucket with the provided credentials and save the new storage backend if successful.

### Use of Storage Backends

A Storage Backend may be used in one of two ways: Either as a Document Storage Backend or a Data Storage Backend. Each method will require the same configuration of a Storage Backend and, in fact, a single Storage Backend may be used for both Documents and Data.

#### Document Storage Backends

Storage Backends used for documents will be read/write. the application will use these backends to save documents using a `dewrangle/uploads/` prefix under the root of the Storage Backend.

#### Data Storage Backends

Storage Backends used for data will only utilize read and list operations. These backends will be used for file discovery and accounting only.

### Setting Organization Storage Backend Defaults

If an organization administrator wishes all new studies to use a given backend for document uploads or data files, they may specify it in the organization settings. The administrator will have two defaults to configure: *Default Document Storage Backend* and *Default Data Storage Backend*. An administrator may use the same Storage Backend for both, but it will be up to them to prevent collisions.

### Changing Storage Backends Per-Study

It may be desirable for a study administrator to use different Storage Backends for different studies. For this, studies will be able to specify one Storage Backend for documents and one or more Storage Backends for data files. 

#### Kids First Example

In Kids First, each study keeps its data in different buckets including documents. If we were to use the Storage Backend approach for Kids First, we could do so by first creating a new Storage Backend for each bucket and then updating each study with the appropriate Storage Backend.
If we would like to stop distributing uploaded documents to each study's bucket, we could simply update each study's Document Storage Backend to use the Default Storage Backend. This would result in all uploaded documents going to the application's bucket with all data operations occurring on each individual study's Data Storage Backend.

### Management of External Buckets

the application will not be responsible for configuration of the external buckets. This responsibility resides with the organization administrator and whoever controls their resources.

## User Flows

### Creating a Storage Backend

Go to organiztion study page and add a new Storage Backend

User provides basic information such as the bucket name and what prefix they want to keep data under
![](https://i.ibb.co/KwZbzdr/Basic.png)

The user will be asked to configure an IAM user within their AWS account that the API may use to interact with the specified bucket.
![](https://i.ibb.co/ys5xc61/Create-User.png)

The user will need to create a new programmatic IAM user within the AWS dashboard

![](https://i.ibb.co/7bVWVFR/Screenshot-2021-08-10-at-15-47-08-IAM-Management-Console.png)

The policy that is suggested or one that allows for similar access will need to be created to be attached to the new IAM user
![](https://i.ibb.co/zQhnYT5/Screenshot-2021-08-10-at-15-51-49-IAM-Management-Console.png)

The new IAM user can then be created
![](https://i.ibb.co/zhj02jx/Screenshot-2021-08-10-at-15-52-42-IAM-Management-Console.png)

In the application, the user may now paste in the credentials for the new IAM user
![](https://i.ibb.co/yBXbjTJ/Create-User-1.png)

Once this is done, the application will confirm that it has the permissions necessary to perform its operations

![](https://i.ibb.co/1fk2B48/Create-User-3.png)

The new storage backend will now be available for use in studies within the organization.


### Modifying Storage Backends for Studies

Study administrators may change a study's settings to use any Storage Backend that is in the organization.
![](https://i.ibb.co/DQZTKCr/Screen-Shot-2021-08-10-at-4-16-15-PM.png)

A study may only have one Document Storage Backend to read and write uploaded documents to. If this location changes after uploads have been made, the application will not be able to find old files unless they are migrated to the correct location in the new backend and updated in the application database. It may be possible to automate this in the future.

[========]


## Technical Implementation

### StorageBackend Model

The storage backend model

```graphql
type StorageBackend {
  id: ID!
  name: String!
  bucket: String
  prefix: String
  organization: Organization
  accessKey: String
  secretKey: String
  arn: String
  account_id: Int
  account_alias: String
  user: String
}
```

#### Secret Storage

The `access_key` and `secret_key` will be stored in the application's database in an encrypted state. The encryption will be done with a KMS key provisioned specifically for the application. In order to perform actions on behalf of the IAM user and thus the stored key pair, the secrets must be decrypted first using the same KMS key.

#### Blank Secrets

The secret key pair is *optional*. This is to allow other access methods such as direct modification of the application's IAM user.
For example, the application's IAM user may already be granted access to a bucket location through its policy. To create a storage backend that utilizes this location requires only that the application be informed of the the bucket and prefix. No new access credentials will be required as the application will use its IAM user to try to access the location by default.

### Mutations

#### Create

```graphql
type CreateStorageBackendInput {
  name: String!
  bucket: String!
  prefix: String
  organization: ID!
  accessKey: String
  secretKey: String
  healthy: Bool!
}
createStorageBackend(input: CreateStorageBackendInput): StorageBackend!
```
Only organization administrators may be allowed to create new storage backends.
The create mutation includes an attempt to verify that the application has proper access to the specified resource and desired actions.

#### Update

```graphql
type UpdateStorageBackendInput {
  name: String!
  accessKey: String
  secretKey: String
}
updateStorageBackend(id: ID!, input: UpdateStorageBackendInput): StorageBackend!
```
Only organization administrators may be allowed to update Storage Backends. If the secrets are being updated, the validity of the access will be checked.

#### Delete

```graphql
deleteStorageBackend(id: ID!): StorageBackend!
```
Only Organization administrators may be allowed to delete existing storage backends in their Organization. This will remove the Storage Backend and its secrets entirely from the database. Any studies that use the Storage Backend will be reset to the default the application Storage.

#### Update Storages

```graphql
type UpdateStoragesInput {
  documentBucket: ID
  dataBuckets: [ID]
}
updateStorages(id: ID!, input: UpdateStorageBackendInput): Study!
```

This mutation allows a user to change the Storage Backend configuration for a study.

### Updates to the Study Model

The study model will take on two new relationships:

```graphql
type Study {
  ...existing study fields
  documentStorage: StorageBackend
  dataStorage: [StorageBackend]
}
```

### Updates to Study Creation

Because all future studies will utilize the default storage backend, it will no longer be necessary to setup new buckets for each study. To disable this behavior, the `FEAT_STUDY_BUCKETS_CREATE_BUCKETS` setting may simply be set to `False` or we may choose to make it an option in the mutation or remove the code alltogether.

### Updates to Download Views

Download views will first need to lookup a requested file's Storage Backend through association with its study. This will then require decrypting secrets and using the IAM user to retrieve the requested file.

### Updates to Upload Mutations

Upload mutations for new documents and versions will need to be updated to retrieve the related Storage Backend's credentials to write files as needed.

### Updates to Other File Access

> TODO
>
> File access should hopefully be transparant through implementing a custom Django storage backend that will retrieve credentials automatically making any necessary file access work seamlessly.

### Default Storage

A default storage location will be provisioned for each Organization in the application. This location will reside within the application bucket provisioned for the application. A prefix will be designated for the organization and the access credentials will be blank as the application's IAM policy will allow the correct access.

### Periodic Maintenance

It may be desireable to have a daily occuring task that will perform verification that each Storage Backend has keys that are actively attached to a user with the desired access. If a Storage Backend ever has issues comunicating with the provided credentials, it may be most helpful to send an automated email to an Organization administrator to remedy the problem.

## Migrating

### Existing Study Buckets

Existing study buckets will need to be added as storage backends in the application. These storage backends will not require new IAM users to be created as the application's IAM profile should still contain the permissions needed to access them. from here, existing files should be retrievable to the application in their original location although new uploads may have the new root prefix prepended (`dewrangle/uploads/`)

### Moving to the Default Storage

It may be desirable to relocate all documents uploaded to the application within the default storage. To do this, the following would need to be performed in order:

1 - Copy files out of `uploads` directories in study buckets to `dewrangle/<study_id>/uploads/`
2 - Update paths of existing files in database to point to new location
3 - Remove files from old upload location in study buckets


### Relocating a Study to a New Storage Backend

There may be a request to change a study's document storage backend after that study has recieved documents. This request should be fullfilled but with clear warnings that doing so will cause previously uploaded files to become unretrievable. The user may ask for support in moving their document from the old storage backend to the new one. In this case, a similar procedure to that outlined above may be followed manually.

### Facilitating Future Migrations

If changing document storage backends becomes a task performed frequently over the course of a study's life, we may wish to automate some of the process. This automation would need to automatically copy documents between storage backends and update their paths within the database. This could be tricky as it would require accessing data in one backend using one user and writing it to a different backend with another user.
