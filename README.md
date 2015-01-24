These instructions show how to both create a *trusted* IAM role (likely in 
the moz-opsec AWS account) and a *trusting* IAM role in foreign AWS accounts. 
This will allow other Mozilla teams with AWS accounts to delegate permissions 
to OpSec to enable OpSec to perform security audits.

The policy in the *trusting* account contains a list of permissions which come 
from the AWS built in "Security Audit" IAM role.

# Trusting Account

Here's how to create an IAM role for the trusting account. This would be done 
by a foreign AWS account holder who wants to grant OpSec the ability to audit 
the security of their AWS account.

## Create a Trusting Account using cloudformation

This method is preferred over using boto.

* The foreign AWS account holder should log into their AWS web console
* Browse to the [CloudFormation section](https://console.aws.amazon.com/cloudformation/home?region=us-west-2)
* Click the `Create Stack` button
  * In the `Name` field enter something like `opsec-security-audit-role`
  * In the `Source` field select `Specify an Amazon S3 template URL` and type in 
 
    https://s3-us-west-2.amazonaws.com/opsec-cloudformation-templates/opsec-security-audit-trusting-role-cloudformation.json

* Click the `Next` button
* Deploy the `opsec-security-audit-trusting-role-cloudformation.json` template
* On the `Options` page click the `Next` button
* On the `Review` page click the checkbox that says `I acknowledge that this template might cause AWS CloudFormation to create IAM resources.`
* Click the `Create` button
* When the CloudFormation stack completes the creation process and the `Status` field changes from `CREATE_IN_PROGRESS` to `CREATE_COMPLETE`, select the new stack and click the `Outputs` tab in the bottom window pane.
* Copy the `Value` given for the `OpSecSecurityAuditRoleARN` `Key` and paste it into the bug that OpSec opened requesting the creation of this account
  * An example `Value` would be `arn:aws:iam::123456789012:role/opsec-security-audit-role-OpSecSecurityAuditRole-1234567890AB`

## Create a Trusting Account using boto

This is not the preferred method to grant these rights. The cloudformation template described later
is preferred.

```
#!/usr/bin/env python

# Set this to the ARN of the trusted account role
trusted_account_role_arn="arn:aws:iam::656532927350:role/OpSecTrustedAuditor"

import boto.iam
conn_iam = boto.iam.connect_to_region('universal')
role_name='OpSecSeucrityAudit'
instance_profile_name='OpSecSeucrityAuditInstanceProfile'
assume_role_policy_document = '''{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"",
      "Effect":"Allow",
      "Principal":{
        "AWS":"%s"
      },
      "Action":"sts:AssumeRole"
    }
  ]
}''' % trusted_account_role_arn
policy_name = "SecurityAudit"
policy_document = '''{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "autoscaling:Describe*",
        "cloudformation:DescribeStack*",
        "cloudformation:GetTemplate",
        "cloudformation:ListStack*",
        "cloudfront:Get*",
        "cloudfront:List*",
        "cloudwatch:Describe*",
        "directconnect:Describe*",
        "dynamodb:ListTables",
        "ec2:Describe*",
        "elasticbeanstalk:Describe*",
        "elasticache:Describe*",
        "elasticloadbalancing:Describe*",
        "elasticmapreduce:DescribeJobFlows",
        "glacier:ListVaults",
        "iam:Get*",
        "iam:List*",
        "rds:Describe*",
        "rds:DownloadDBLogFilePortion",
        "rds:ListTagsForResource",
        "redshift:Describe*",
        "route53:GetHostedZone",
        "route53:ListHostedZones",
        "route53:ListResourceRecordSets",
        "s3:GetBucket*",
        "s3:GetLifecycleConfiguration",
        "s3:GetObjectAcl",
        "s3:GetObjectVersionAcl",
        "s3:ListAllMyBuckets",
        "sdb:DomainMetadata",
        "sdb:ListDomains",
        "sns:GetTopicAttributes",
        "sns:ListTopics",
        "sqs:GetQueueAttributes",
        "sqs:ListQueues"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}'''

print(conn_iam.create_role(role_name=role_name,
      assume_role_policy_document=assume_role_policy_document))

print(conn_iam.put_role_policy(role_name=role_name,
      policy_name=policy_name,
      policy_document=policy_document))
print(conn_iam.create_instance_profile(instance_profile_name))
print(conn_iam.add_role_to_instance_profile(instance_profile_name,
                                            role_name))

```

# Trusted account

This IAM role is created in an OpSec controlled AWS account (likely the 
moz-opsec account) and is the role which the *trusting* accounts delegate
permissions to.

Note, since the trusted account must have a predictable ARN to be referenced
by the *trusting* accounts it can not be created with cloudformation.

```
import boto.iam
conn_iam = boto.iam.connect_to_region('universal')
role_name='OpSecTrustedAuditor'
instance_profile_name='OpSecTrustedAuditorInstanceProfile'
assume_role_policy_document = '''{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'''
policy_name = 'OpSecTrustedAuditorPerms'
policy_document = '''{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "*"
    }
  ]
}'''

print(conn_iam.create_role(role_name=role_name,
                           assume_role_policy_document=assume_role_policy_document))
print(conn_iam.put_role_policy(role_name=role_name,
                               policy_name=policy_name,
                               policy_document=policy_document))
print(conn_iam.create_instance_profile(instance_profile_name))
print(conn_iam.add_role_to_instance_profile(instance_profile_name,
                                            role_name))
```

## Trusted account instance

To create an ec2 instance that has the trusted account IAM role, launch the
`opsec-security-auditor-cloudformation.json` cloudformation template in the
OpSec controlled AWS account in which the `OpSecTrustedAuditor` IAM role and
`OpSecTrustedAuditorInstanceProfile` instance profile were created in.
