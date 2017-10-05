# `build_cloudtrail_storage`

This tool provisioned CloudTrail storage in the Mozilla Secure CloudTrail Storage System version 1. Since then we've moved to a new model which

* utilizes the [December 2015](https://aws.amazon.com/blogs/aws/aws-cloudtrail-update-turn-on-in-all-regions-use-multiple-trails/) CloudTrail product update allowing for multiple trails
* expects AWS account holders to setup their own additional CloudTrail trails if they would like access to CloudTrail data (instead of utilizing IAM Role Assumption to read CloudTrail data stored in the Mozilla Secure CloudTrail Storage System)
* expects AWS account holders to setup their own SNS topics for their own CloudTrail trails instead of needing access to SNS topics in the Mozilla Secure CloudTrail Storage System

As a result of the changes to the CloudTrail AWS product, all of this infrastructure is no longer needed.